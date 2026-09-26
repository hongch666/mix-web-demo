import importlib
from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from app.core.constants import HttpCode, Messages, Prompts
from app.core.errors import BusinessException
from app.internal.services.generate.generateService import GenerateService

generate_module = importlib.import_module(
    "app.internal.services.generate.generateService"
)


def _make_service(glm=None, gemini=None, gpt=None, spring=None) -> GenerateService:
    return GenerateService(
        glm_service=glm,
        gemini_service=gemini,
        gpt_service=gpt,
        spring_client=spring if spring is not None else AsyncMock(),
    )


def _llm_service(
    *,
    basic_result: str | None = None,
    basic_error: Exception | None = None,
    reference_result: str | None = None,
    reference_error: Exception | None = None,
    summarize_result: str | None = None,
    summarize_error: Exception | None = None,
) -> AsyncMock:
    llm = AsyncMock()
    llm.basic_chat = AsyncMock(return_value=basic_result, side_effect=basic_error)
    llm.with_reference_chat = AsyncMock(
        return_value=reference_result, side_effect=reference_error
    )
    llm.summarize_content = AsyncMock(
        return_value=summarize_result, side_effect=summarize_error
    )
    return llm


def _comments_by_user(spring: AsyncMock) -> dict[int, dict]:
    return {
        call.args[0]["user_id"]: call.args[0]
        for call in spring.create_comment.await_args_list
    }


# ===== 关键词提取 =====


# 提取关键词前清洗 Markdown 符号并透传 topK
@pytest.mark.anyio
async def test_extract_tags_strips_markdown_symbols(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_extract(text: str, topK: int = 5) -> list[str]:
        captured["text"] = text
        captured["topK"] = topK
        return ["tag1", "tag2"]

    monkeypatch.setattr(generate_module.jieba.analyse, "extract_tags", fake_extract)
    service = _make_service()

    result = await service.extract_tags("# 标题\n\n```code```\n**粗体** 正文", topK=2)

    assert result == "tag1,tag2"
    assert captured["topK"] == 2
    cleaned = str(captured["text"])
    assert "#" not in cleaned
    assert "`" not in cleaned
    assert "*" not in cleaned
    assert "\n" not in cleaned
    assert "标题" in cleaned


# ===== 评论文本构造与解析 =====


# 评论数据使用下划线字段契约并写入一致的创建更新时间
def test_build_comment_data_uses_snake_case_contract() -> None:
    data = GenerateService._build_comment_data(5, 1001, "内容", 8.5)

    assert set(data) == {
        "article_id",
        "user_id",
        "content",
        "star",
        "create_time",
        "update_time",
    }
    assert data["article_id"] == 5
    assert data["user_id"] == 1001
    assert data["content"] == "内容"
    assert data["star"] == 8.5
    assert data["create_time"] == data["update_time"]
    assert datetime.fromisoformat(data["create_time"])


# 解析模型评分文本，覆盖带标记与纯文本多种格式
@pytest.mark.parametrize(
    ("response", "expected_content", "expected_star"),
    [
        ("评价内容：很好\n评分：8.5", "很好", 8.5),
        ("评分：7", "评分：7", 7.0),
        ("这篇文章非常好 9分", "这篇文章非常好 9分", 9.0),
        ("完全无关的内容", "完全无关的内容", 6.0),
    ],
)
def test_parse_ai_comment_response_variants(
    response: str, expected_content: str, expected_star: float
) -> None:
    service = _make_service()

    content, star = service._parse_ai_comment_response(response)

    assert content == expected_content
    assert star == expected_star


# 无评分标记的超长文本截断为 200 字并给默认分
def test_parse_ai_comment_response_truncates_long_unmarked_text() -> None:
    service = _make_service()

    content, star = service._parse_ai_comment_response("a" * 500)

    assert content == "a" * 200
    assert star == 6.0


# ===== AI 评论生成 =====


# 存在旧评论时先删除再写入三条各模型评论
@pytest.mark.anyio
async def test_generate_ai_comments_replaces_existing_and_saves_three() -> None:
    spring = AsyncMock()
    spring.get_ai_comments_num_by_article_id.return_value = 2
    spring.get_articles_by_ids.return_value = [
        {"title": "t", "tags": "a", "content": "c"}
    ]
    glm = _llm_service(basic_result="评价内容：g\n评分：7")
    gemini = _llm_service(basic_result="评价内容：m\n评分：8")
    gpt = _llm_service(basic_result="评价内容：p\n评分：9")
    service = _make_service(glm=glm, gemini=gemini, gpt=gpt, spring=spring)

    await service.generate_ai_comments(3)

    spring.delete_ai_comments_by_article_id.assert_awaited_once_with(3)
    assert spring.create_comment.await_count == 3
    by_user = _comments_by_user(spring)
    assert by_user[1001]["content"] == "g"
    assert by_user[1001]["star"] == 7
    assert by_user[1002]["star"] == 8
    assert by_user[1003]["star"] == 9
    assert glm.basic_chat.await_args.args[0] == Prompts.ARTICLE_EVALUATION(
        "t", "a", "c"
    )


# 无旧评论时不执行删除，仍写入三条评论
@pytest.mark.anyio
async def test_generate_ai_comments_skips_delete_without_existing() -> None:
    spring = AsyncMock()
    spring.get_ai_comments_num_by_article_id.return_value = 0
    spring.get_articles_by_ids.return_value = [{"title": "t"}]
    service = _make_service(
        glm=_llm_service(basic_result="评价内容：g\n评分：7"),
        gemini=_llm_service(basic_result="评价内容：m\n评分：8"),
        gpt=_llm_service(basic_result="评价内容：p\n评分：9"),
        spring=spring,
    )

    await service.generate_ai_comments(3)

    spring.delete_ai_comments_by_article_id.assert_not_awaited()
    assert spring.create_comment.await_count == 3


# 文章不存在时抛出 404 文章未找到业务异常
@pytest.mark.anyio
async def test_generate_ai_comments_raises_when_article_missing() -> None:
    spring = AsyncMock()
    spring.get_ai_comments_num_by_article_id.return_value = 0
    spring.get_articles_by_ids.return_value = []
    service = _make_service(spring=spring)

    with pytest.raises(BusinessException) as error:
        await service.generate_ai_comments(99)

    assert error.value.status_code == HttpCode.NOT_FOUND
    assert error.value.error == Messages.ERROR_ARTICLE_NOT_FOUND


# 单个模型失败时该条评论降级为失败文案与默认分，其余正常
@pytest.mark.anyio
async def test_generate_ai_comments_degrades_when_one_model_fails() -> None:
    spring = AsyncMock()
    spring.get_ai_comments_num_by_article_id.return_value = 0
    spring.get_articles_by_ids.return_value = [
        {"title": "t", "tags": "a", "content": "c"}
    ]
    service = _make_service(
        glm=_llm_service(basic_error=RuntimeError("glm down")),
        gemini=_llm_service(basic_result="评价内容：m\n评分：8"),
        gpt=_llm_service(basic_result="评价内容：p\n评分：9"),
        spring=spring,
    )

    await service.generate_ai_comments(3)

    assert spring.create_comment.await_count == 3
    by_user = _comments_by_user(spring)
    assert by_user[1001]["content"] == Messages.GLM_CALL_FAILED_ERROR
    assert by_user[1001]["star"] == 6.0
    assert by_user[1002]["star"] == 8


# 模型未注入时对应评论降级为失败文案
@pytest.mark.anyio
async def test_generate_ai_comments_degrades_when_model_not_injected() -> None:
    spring = AsyncMock()
    spring.get_ai_comments_num_by_article_id.return_value = 0
    spring.get_articles_by_ids.return_value = [
        {"title": "t", "tags": "a", "content": "c"}
    ]
    service = _make_service(
        glm=None,
        gemini=_llm_service(basic_result="评价内容：m\n评分：8"),
        gpt=_llm_service(basic_result="评价内容：p\n评分：9"),
        spring=spring,
    )

    await service.generate_ai_comments(3)

    by_user = _comments_by_user(spring)
    assert by_user[1001]["content"] == Messages.GLM_CALL_FAILED_ERROR
    assert by_user[1002]["star"] == 8


# 后台评论入口转发到评论生成并透传文章 ID
@pytest.mark.anyio
async def test_background_comment_wrapper_delegates() -> None:
    service = _make_service()
    service.generate_ai_comments = AsyncMock()  # type: ignore[method-assign]

    await service.generate_ai_comments_in_background(7)

    service.generate_ai_comments.assert_awaited_once_with(7)


# ===== 基于参考文本的 AI 评论 =====


# 参考评论在文章缺失时直接返回且不调用模型与写入
@pytest.mark.anyio
async def test_generate_ai_comments_with_reference_returns_when_article_missing() -> (
    None
):
    spring = AsyncMock()
    spring.get_ai_comments_num_by_article_id.return_value = 0
    spring.get_articles_by_ids.return_value = []
    glm = _llm_service()
    service = _make_service(glm=glm, spring=spring)

    await service.generate_ai_comments_with_reference(99)

    glm.with_reference_chat.assert_not_awaited()
    spring.create_comment.assert_not_awaited()


# 参考评论先摘要三模型输出再合并作为参考内容
@pytest.mark.anyio
async def test_generate_ai_comments_with_reference_summarizes_reference(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spring = AsyncMock()
    spring.get_ai_comments_num_by_article_id.return_value = 0
    spring.get_articles_by_ids.return_value = [
        {"sub_category_id": 11, "title": "t", "tags": "a", "content": "c"}
    ]
    spring.get_category_reference_by_sub_category_id.return_value = {
        "type": "link",
        "link": "http://ref",
    }

    class _FakeExtractor:
        def __init__(self) -> None:
            self.calls: list[tuple] = []

        async def extract_reference_content(
            self, ref_type, ref_value, max_length, summarizer
        ):  # noqa: ANN001
            self.calls.append((ref_type, ref_value, max_length))
            return await summarizer(ref_value)

    extractor = _FakeExtractor()
    monkeypatch.setattr(
        generate_module, "get_reference_content_extractor", lambda: extractor
    )

    glm = _llm_service(
        summarize_result="glm-sum", reference_result="评价内容：G\n评分：7"
    )
    gemini = _llm_service(
        summarize_result="gemini-sum", reference_result="评价内容：M\n评分：8"
    )
    gpt = _llm_service(
        summarize_result="gpt-sum", reference_result="评价内容：P\n评分：9"
    )
    service = _make_service(glm=glm, gemini=gemini, gpt=gpt, spring=spring)

    await service.generate_ai_comments_with_reference(3)

    assert extractor.calls == [("link", "http://ref", 3000)] * 3
    spring.get_category_reference_by_sub_category_id.assert_awaited_once_with(11)
    article_content, reference_content = glm.with_reference_chat.await_args.args
    assert article_content == Prompts.ARTICLE_REFERENCE_CONTENT("t", "a", "c")
    assert reference_content == "\n\n".join(
        [
            Messages.LLM_SUMMARY_RESULT_ENTRY("GLM", "glm-sum"),
            Messages.LLM_SUMMARY_RESULT_ENTRY("Gemini", "gemini-sum"),
            Messages.LLM_SUMMARY_RESULT_ENTRY("GPT", "gpt-sum"),
        ]
    )
    assert spring.create_comment.await_count == 3


# 缺少子分类时不查询参考内容而使用默认提示
@pytest.mark.anyio
async def test_generate_ai_comments_with_reference_uses_default_without_sub_category() -> (
    None
):
    spring = AsyncMock()
    spring.get_ai_comments_num_by_article_id.return_value = 0
    spring.get_articles_by_ids.return_value = [
        {"title": "t", "tags": "a", "content": "c"}
    ]
    glm = _llm_service(reference_result="评价内容：G\n评分：7")
    service = _make_service(glm=glm, spring=spring)

    await service.generate_ai_comments_with_reference(3)

    assert glm.with_reference_chat.await_args.args[1] == (
        Messages.CATEGORY_NO_AUTHORITATIVE_REFERENCE_TEXT_ERROR
    )
    spring.get_category_reference_by_sub_category_id.assert_not_awaited()


# 参考内容抽取为空时回退为原始链接文案
@pytest.mark.anyio
async def test_generate_ai_comments_with_reference_falls_back_when_extraction_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spring = AsyncMock()
    spring.get_ai_comments_num_by_article_id.return_value = 0
    spring.get_articles_by_ids.return_value = [
        {"sub_category_id": 11, "title": "t", "tags": "a", "content": "c"}
    ]
    spring.get_category_reference_by_sub_category_id.return_value = {
        "type": "link",
        "link": "http://ref",
    }

    class _FakeExtractor:
        async def extract_reference_content(
            self, ref_type, ref_value, max_length, summarizer
        ):  # noqa: ANN001
            return ""

    monkeypatch.setattr(
        generate_module, "get_reference_content_extractor", lambda: _FakeExtractor()
    )

    glm = _llm_service(reference_result="评价内容：G\n评分：7")
    service = _make_service(glm=glm, spring=spring)

    await service.generate_ai_comments_with_reference(3)

    expected = Messages.REFERENCE_TEXT_FALLBACK_CONTENT("link", "http://ref")
    assert glm.with_reference_chat.await_args.args[1] == expected


# ===== 权威文章总结 =====


# 不支持的参考类型直接返回错误状态与提示
@pytest.mark.anyio
async def test_generate_authority_article_rejects_unsupported_type(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        generate_module, "get_reference_content_extractor", lambda: AsyncMock()
    )
    service = _make_service()

    result = await service.generate_authority_article_with_ai_summaries("video", "x")

    assert result == {
        "status": "error",
        "message": Messages.UNSUPPORTED_REFERENCE_TYPE("video"),
    }


# 链接类型抽取正文后返回三模型摘要与正文预览信息
@pytest.mark.anyio
async def test_generate_authority_article_link_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _FakeExtractor:
        def __init__(self) -> None:
            self.link_calls: list[tuple] = []

        async def extract_link_content(self, value, max_length=3000):  # noqa: ANN001
            self.link_calls.append((value, max_length))
            return "raw content"

    extractor = _FakeExtractor()
    monkeypatch.setattr(
        generate_module, "get_reference_content_extractor", lambda: extractor
    )
    service = _make_service(
        glm=_llm_service(summarize_result="s1"),
        gemini=_llm_service(summarize_result="s2"),
        gpt=_llm_service(summarize_result="s3"),
    )

    result = await service.generate_authority_article_with_ai_summaries(
        "Link", "http://doc"
    )

    assert extractor.link_calls == [("http://doc", 3000)]
    assert result["status"] == "success"
    assert result["reference_type"] == "Link"
    assert result["reference_value"] == "http://doc"
    assert result["raw_content_length"] == len("raw content")
    assert result["raw_content_preview"] == "raw content"
    assert result["summaries"]["glm"] == {"content": "s1", "length": 2}
    assert result["summaries"]["gemini"] == {"content": "s2", "length": 2}
    assert result["summaries"]["gpt"] == {"content": "s3", "length": 2}


# PDF 正文抽取为空时返回抽取失败错误
@pytest.mark.anyio
async def test_generate_authority_article_pdf_empty_returns_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _FakeExtractor:
        async def extract_pdf_content(self, value, max_length=3000):  # noqa: ANN001
            return None

    monkeypatch.setattr(
        generate_module, "get_reference_content_extractor", lambda: _FakeExtractor()
    )
    service = _make_service()

    result = await service.generate_authority_article_with_ai_summaries(
        "pdf", "doc.pdf"
    )

    assert result == {
        "status": "error",
        "message": Messages.REFERENCE_TEXT_EXTRACTION_ERROR,
    }


# 部分模型摘要失败仍返回成功并标记该模型空摘要
@pytest.mark.anyio
async def test_generate_authority_article_partial_summary_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _FakeExtractor:
        async def extract_link_content(self, value, max_length=3000):  # noqa: ANN001
            return "raw"

    monkeypatch.setattr(
        generate_module, "get_reference_content_extractor", lambda: _FakeExtractor()
    )
    service = _make_service(
        glm=_llm_service(summarize_error=RuntimeError("glm down")),
        gemini=_llm_service(summarize_result="s2"),
        gpt=_llm_service(summarize_result="s3"),
    )

    result = await service.generate_authority_article_with_ai_summaries(
        "link", "http://doc"
    )

    assert result["status"] == "success"
    assert result["summaries"]["glm"] == {"content": None, "length": 0}
    assert result["summaries"]["gemini"]["content"] == "s2"


# 正文抽取抛错时返回包含原始错误的生成失败信息
@pytest.mark.anyio
async def test_generate_authority_article_wraps_extraction_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _FakeExtractor:
        async def extract_link_content(self, value, max_length=3000):  # noqa: ANN001
            raise RuntimeError("extract boom")

    monkeypatch.setattr(
        generate_module, "get_reference_content_extractor", lambda: _FakeExtractor()
    )
    service = _make_service()

    result = await service.generate_authority_article_with_ai_summaries(
        "link", "http://doc"
    )

    assert result["status"] == "error"
    assert result["message"] == Messages.AUTHORITY_ARTICLE_GENERATION_FAILED(
        "extract boom"
    )
