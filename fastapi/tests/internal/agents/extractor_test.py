"""ReferenceContentExtractor 文本提取与降级逻辑的单元测试"""

from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest
from langchain_core.documents import Document

from app.core.constants import Defaults
from app.internal.agents import extractor as extractor_module
from app.internal.agents.extractor import (
    ReferenceContentExtractor,
    get_reference_content_extractor,
)


class _FakeSplitter:
    def __init__(
        self, chunks: list[str] | None = None, error: Exception | None = None
    ) -> None:
        self._chunks = chunks or []
        self._error = error

    def split_documents(self, documents: list[Document]) -> list[Document]:
        if self._error is not None:
            raise self._error
        return [Document(page_content=chunk) for chunk in self._chunks]


class _FakeResponse:
    def __init__(self, text: str = "", error: Exception | None = None) -> None:
        self.text = text
        self._error = error

    def raise_for_status(self) -> None:
        if self._error is not None:
            raise self._error


class _FakeLinkClient:
    def __init__(self, response: _FakeResponse) -> None:
        self.get = AsyncMock(return_value=response)

    async def __aenter__(self) -> "_FakeLinkClient":
        return self

    async def __aexit__(self, *args: Any) -> bool:
        return False


# HTML 标签与多余空白混合输入被清洗为单空格分隔的纯文本
def test_clean_text_removes_markup_and_collapses_whitespace() -> None:
    cleaned = ReferenceContentExtractor._clean_text(
        "<h1>标题</h1>\n\n   正文   内容   "
    )

    assert cleaned == "标题 正文 内容"


# 空字符串输入经清洗后仍返回空字符串
def test_clean_text_returns_empty_for_falsy_input() -> None:
    assert ReferenceContentExtractor._clean_text("") == ""


# 含概念、原理关键词的文本优先抽取关键词句并拼接
def test_extract_key_points_prefers_keyword_sentences() -> None:
    text = "这是一个概念。无关的句子。另一个原理的说明。"

    assert (
        ReferenceContentExtractor._extract_key_points(text)
        == "这是一个概念。另一个原理的说明"
    )


# 指定 max_length 时抽取结果被截断到该长度
def test_extract_key_points_truncates_to_max_length() -> None:
    text = "定义" + "很长的说明文本" * 10

    result = ReferenceContentExtractor._extract_key_points(text, max_length=10)

    assert len(result) == 10


# 无关键词时退化为按段落拼接并补全句号
def test_extract_key_points_falls_back_to_paragraphs_without_keywords() -> None:
    text = "第一段内容\n\n第二段内容"

    assert (
        ReferenceContentExtractor._extract_key_points(text) == "第一段内容。第二段内容"
    )


# 空白文本抽取关键词要点时返回空字符串
def test_extract_key_points_returns_empty_for_blank_text() -> None:
    assert ReferenceContentExtractor._extract_key_points("") == ""


# 替换配置的分割器后按分割器返回的文本块列表返回
def test_split_text_uses_configured_splitter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        ReferenceContentExtractor, "TEXT_SPLITTER", _FakeSplitter(["块1", "块2"])
    )

    assert ReferenceContentExtractor.split_text("原始长文本") == ["块1", "块2"]


# 分割器初始化抛异常时返回原文且不缓存分割器实例
def test_split_text_returns_original_when_splitter_init_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _RaisingSplitter:
        def __init__(self, **kwargs: Any) -> None:
            raise RuntimeError("splitter init failed")

    monkeypatch.setattr(ReferenceContentExtractor, "TEXT_SPLITTER", None)
    monkeypatch.setattr(
        extractor_module, "RecursiveCharacterTextSplitter", _RaisingSplitter
    )

    assert ReferenceContentExtractor.split_text("无法分割的文本") == ["无法分割的文本"]
    assert ReferenceContentExtractor.TEXT_SPLITTER is None


# 分块过程抛异常时降级返回原文组成的单元素列表
def test_split_text_returns_original_when_split_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        ReferenceContentExtractor,
        "TEXT_SPLITTER",
        _FakeSplitter(error=RuntimeError("split failed")),
    )

    assert ReferenceContentExtractor.split_text("原始文本") == ["原始文本"]


# 存在共享 HTTP 客户端时复用并按默认请求头抓取链接正文
@pytest.mark.anyio
async def test_link_content_uses_shared_client_and_cleans_html(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _FakeLinkClient(_FakeResponse("<p>概念定义说明</p>"))
    monkeypatch.setattr(extractor_module, "get_shared_http_client", lambda: client)

    result = await ReferenceContentExtractor.extract_link_content(
        "http://example.com/a"
    )

    assert "概念定义说明" in result
    call = client.get.await_args
    assert call.args[0] == "http://example.com/a"
    assert call.kwargs["headers"] == Defaults.EXTRACTOR_REQUEST_HEADERS


# 无共享客户端时临时创建 AsyncClient 抓取并只调用一次
@pytest.mark.anyio
async def test_link_content_falls_back_to_temporary_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    temp_client = _FakeLinkClient(_FakeResponse("<p>知识图谱召回</p>"))
    monkeypatch.setattr(extractor_module, "get_shared_http_client", lambda: None)
    monkeypatch.setattr(
        extractor_module,
        "httpx",
        SimpleNamespace(AsyncClient=lambda timeout=None: temp_client),
    )

    result = await ReferenceContentExtractor.extract_link_content(
        "http://example.com/b"
    )

    assert "知识图谱召回" in result
    temp_client.get.assert_awaited_once()


# 请求异常时链接抓取降级返回空字符串
@pytest.mark.anyio
async def test_link_content_returns_empty_on_request_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _FakeLinkClient(_FakeResponse(error=RuntimeError("network down")))
    monkeypatch.setattr(extractor_module, "get_shared_http_client", lambda: client)

    assert (
        await ReferenceContentExtractor.extract_link_content("http://example.com/c")
        == ""
    )


# URL 为空时直接返回空字符串且不发起请求
@pytest.mark.anyio
async def test_link_content_returns_empty_for_blank_url() -> None:
    assert await ReferenceContentExtractor.extract_link_content("") == ""


class _FakeAsyncFile:
    def __init__(self) -> None:
        self.chunks: list[bytes] = []

    async def write(self, chunk: bytes) -> None:
        self.chunks.append(chunk)


class _FakeOpenFile:
    def __init__(self, file: _FakeAsyncFile) -> None:
        self._file = file

    def __await__(self):
        async def _result() -> "_FakeOpenFile":
            return self

        return _result().__await__()

    async def __aenter__(self) -> _FakeAsyncFile:
        return self._file

    async def __aexit__(self, *args: Any) -> bool:
        return False


class _FakePdfResponse:
    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    async def aiter_bytes(self):
        yield self._payload


class _FakePdfStream:
    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    async def __aenter__(self) -> _FakePdfResponse:
        return _FakePdfResponse(self._payload)

    async def __aexit__(self, *args: Any) -> bool:
        return False


class _FakePdfAsyncClientWithBytes:
    def __init__(self, timeout: float | None = None) -> None:
        self.timeout = timeout

    async def __aenter__(self) -> "_FakePdfAsyncClientWithBytes":
        return self

    async def __aexit__(self, *args: Any) -> bool:
        return False

    def stream(self, method: str, url: str) -> _FakePdfStream:
        return _FakePdfStream(b"%PDF-1.4 fake")


class _FakePyPDFLoader:
    def __init__(self, path: str) -> None:
        self.path = path

    def load(self) -> list[Document]:
        return [Document(page_content="概念定义很重要。无关句子。")]


class _FailingPyPDFLoader:
    def __init__(self, path: str) -> None:
        self.path = path

    def load(self) -> list[Document]:
        raise RuntimeError("pdf parse failed")


# PDF 下载写入临时文件解析后用哈希路径清理临时文件
@pytest.mark.anyio
async def test_pdf_content_downloads_parses_and_cleans_up(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    written = _FakeAsyncFile()
    cleanup = Mock()
    monkeypatch.setattr(
        extractor_module,
        "httpx",
        SimpleNamespace(AsyncClient=_FakePdfAsyncClientWithBytes),
    )
    monkeypatch.setattr(
        extractor_module,
        "anyio",
        SimpleNamespace(open_file=lambda path, mode: _FakeOpenFile(written)),
    )
    monkeypatch.setattr(extractor_module, "PyPDFLoader", _FakePyPDFLoader)
    monkeypatch.setattr(extractor_module, "_cleanup_temp_file", cleanup)

    result = await ReferenceContentExtractor.extract_pdf_content(
        "http://example.com/a.pdf"
    )

    assert "概念定义很重要" in result
    assert written.chunks == [b"%PDF-1.4 fake"]
    expected_path = Defaults.TEMP_PDF_PATH_TEMPLATE.format(
        hash("http://example.com/a.pdf")
    )
    cleanup.assert_called_once_with(expected_path)


# PDF 解析失败时返回空字符串且仍执行临时文件清理
@pytest.mark.anyio
async def test_pdf_content_returns_empty_when_parsing_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    written = _FakeAsyncFile()
    cleanup = Mock()
    monkeypatch.setattr(
        extractor_module,
        "httpx",
        SimpleNamespace(AsyncClient=_FakePdfAsyncClientWithBytes),
    )
    monkeypatch.setattr(
        extractor_module,
        "anyio",
        SimpleNamespace(open_file=lambda path, mode: _FakeOpenFile(written)),
    )
    monkeypatch.setattr(extractor_module, "PyPDFLoader", _FailingPyPDFLoader)
    monkeypatch.setattr(extractor_module, "_cleanup_temp_file", cleanup)

    assert (
        await ReferenceContentExtractor.extract_pdf_content("http://example.com/b.pdf")
        == ""
    )
    cleanup.assert_called_once()


# pdf 类型先抽取原文再经传入的摘要函数生成最终结果
@pytest.mark.anyio
async def test_reference_content_dispatches_by_type_and_applies_summarizer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        ReferenceContentExtractor,
        "extract_pdf_content",
        AsyncMock(return_value="PDF 原始内容"),
    )
    summarize = AsyncMock(return_value="AI 摘要")

    result = await ReferenceContentExtractor.extract_reference_content(
        "pdf", "http://example.com/a.pdf", summarize_func=summarize
    )

    assert result == "AI 摘要"
    summarize.assert_awaited_once_with("PDF 原始内容")


# 摘要函数异常时降级返回原始抽取内容
@pytest.mark.anyio
async def test_reference_content_falls_back_to_raw_when_summarizer_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        ReferenceContentExtractor,
        "extract_link_content",
        AsyncMock(return_value="链接原始内容"),
    )
    summarize = AsyncMock(side_effect=RuntimeError("llm down"))

    result = await ReferenceContentExtractor.extract_reference_content(
        "link", "http://example.com/a", summarize_func=summarize
    )

    assert result == "链接原始内容"


# 不支持的引用类型直接返回空字符串
@pytest.mark.anyio
async def test_reference_content_returns_empty_for_unsupported_type() -> None:
    assert await ReferenceContentExtractor.extract_reference_content("video", "x") == ""


# 引用值为空时直接返回空字符串
@pytest.mark.anyio
async def test_reference_content_returns_empty_when_empty_value() -> None:
    assert await ReferenceContentExtractor.extract_reference_content("pdf", "") == ""


# 抽取原文为空时不调用摘要函数并返回空字符串
@pytest.mark.anyio
async def test_reference_content_returns_empty_when_no_raw_content(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        ReferenceContentExtractor,
        "extract_pdf_content",
        AsyncMock(return_value=""),
    )

    assert await ReferenceContentExtractor.extract_reference_content("pdf", "url") == ""


# 工厂函数两次调用返回同一缓存的抽取器实例
def test_get_reference_content_extractor_is_cached(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        ReferenceContentExtractor, "_init_text_splitter", classmethod(lambda cls: None)
    )
    get_reference_content_extractor.cache_clear()
    try:
        first = get_reference_content_extractor()
        second = get_reference_content_extractor()
    finally:
        get_reference_content_extractor.cache_clear()

    assert isinstance(first, ReferenceContentExtractor)
    assert first is second
