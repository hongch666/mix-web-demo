import asyncio
import importlib
from collections.abc import AsyncGenerator, AsyncIterator
from typing import Annotated, Any, cast
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.common.decorators import ApiLogConfig, apiLog, log, logWithConfig
from app.core.constants import ErrorCodes, HttpCode, Messages
from app.core.errors import BusinessException

api_log_module = importlib.import_module("app.common.decorators.apiLog")


class _ArticlePayload(BaseModel):
    title: str
    phone: str


class _FakeUploadFile:
    """最小化模拟 UploadFile，仅提供序列化需要的 filename 与 file 属性"""

    def __init__(self, filename: str) -> None:
        self.filename: str = filename
        self.file: bytes = b"binary-content"


def _make_request(
    *,
    method: str = "POST",
    path: str = "/articles/117",
    query: str = "",
    path_params: dict[str, Any] | None = None,
) -> Request:
    return Request(
        {
            "type": "http",
            "method": method,
            "path": path,
            "headers": [],
            "query_string": query.encode(),
            "path_params": path_params or {},
        }
    )


def _patch_dependencies(
    monkeypatch: pytest.MonkeyPatch,
    *,
    user_id: int | None = 7,
    username: str | None = "alice",
    queue_result: bool = True,
) -> AsyncMock:
    monkeypatch.setattr(api_log_module, "Logger", Mock())
    monkeypatch.setattr(api_log_module, "get_current_user_id", lambda: user_id)
    monkeypatch.setattr(api_log_module, "get_current_username", lambda: username)
    queue_send = AsyncMock(return_value=queue_result)
    monkeypatch.setattr(api_log_module, "send_to_queue_async", queue_send)
    return queue_send


def _queue_payload(queue_send: AsyncMock) -> dict[str, Any]:
    assert queue_send.await_args is not None
    assert queue_send.await_args.args[0] == "api-log-queue"
    assert queue_send.await_args.kwargs == {"persistent": True}
    return cast(dict[str, Any], queue_send.await_args.args[1])


# 装饰同步接口时抛 TypeError 提示接口必须为异步
def test_rejects_synchronous_endpoint() -> None:
    def endpoint(value: int) -> int:
        return value

    with pytest.raises(TypeError, match=Messages.APILOG_ASYNC_ERROR):
        apiLog("同步接口")(endpoint)


# 完整记录用户、方法、路径参数、查询参数与请求体到日志队列
def test_records_request_context_and_body(monkeypatch: pytest.MonkeyPatch) -> None:
    queue_send = _patch_dependencies(monkeypatch)
    request = _make_request(query="page=2", path_params={"id": "117"})

    @apiLog("获取文章详情")
    async def get_article(request: Request, body: _ArticlePayload) -> str:
        return "ok"

    assert (
        asyncio.run(
            get_article(request=request, body=_ArticlePayload(title="标题", phone="1"))
        )
        == "ok"
    )

    message = _queue_payload(queue_send)
    assert message["userId"] == 7
    assert message["username"] == "alice"
    assert message["apiDescription"] == "获取文章详情"
    assert message["apiMethod"] == "POST"
    assert message["apiPath"] == "/articles/:id"
    assert message["queryParams"] == {"page": "2"}
    assert message["pathParams"] == {"id": "117"}
    assert message["requestBody"] == {"title": "标题", "phone": "1"}
    assert message["responseTime"] >= 0


# exclude_fields 命中的参数从队列请求体中剔除
def test_exclude_fields_removes_named_parameter_from_queue_body(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    queue_send = _patch_dependencies(monkeypatch)
    request = _make_request()

    @logWithConfig("创建文章", exclude_fields=["body"])
    async def create_article(request: Request, body: _ArticlePayload) -> str:
        return "ok"

    asyncio.run(
        create_article(request=request, body=_ArticlePayload(title="标题", phone="1"))
    )

    message = _queue_payload(queue_send)
    assert message["requestBody"] is None


# 日志行参数提取时排除指定字段且保留其余参数
def test_exclude_fields_removes_named_parameter_from_log_line() -> None:
    async def endpoint(credential: str = "", keyword: str = "") -> None:
        return None

    params_info = api_log_module._extract_params_info(
        endpoint,
        (),
        {"credential": "unit-test-value", "keyword": "python"},
        ["credential"],
    )

    assert "credential" not in params_info
    assert "unit-test-value" not in params_info
    assert "keyword: python" in params_info


# 关闭 include_params 后队列请求体记录为 None
def test_include_params_disabled_skips_request_body(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    queue_send = _patch_dependencies(monkeypatch)
    request = _make_request()

    @logWithConfig("敏感操作", include_params=False)
    async def sensitive_operation(request: Request, body: _ArticlePayload) -> str:
        return "ok"

    asyncio.run(
        sensitive_operation(
            request=request, body=_ArticlePayload(title="标题", phone="1")
        )
    )

    message = _queue_payload(queue_send)
    assert message["requestBody"] is None


# 缺少请求对象时方法与路径回退默认值且参数为空
def test_falls_back_to_default_method_and_path_without_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    queue_send = _patch_dependencies(monkeypatch)

    @log("无请求对象")
    async def ping() -> str:
        return "pong"

    assert asyncio.run(ping()) == "pong"

    message = _queue_payload(queue_send)
    assert message["apiMethod"] == "UNKNOWN"
    assert message["apiPath"] == "/ping"
    assert message["queryParams"] is None
    assert message["pathParams"] is None


# 入队失败不影响接口正常返回响应
def test_queue_failure_does_not_break_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    queue_send = _patch_dependencies(monkeypatch, queue_result=False)

    @apiLog("队列失败")
    async def endpoint(request: Request) -> str:
        return "ok"

    assert asyncio.run(endpoint(request=_make_request())) == "ok"
    queue_send.assert_awaited_once()


# 业务异常向上抛出且不写入日志队列
def test_business_exception_propagates_without_queue_send(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    queue_send = _patch_dependencies(monkeypatch)

    @apiLog("业务异常")
    async def failing(request: Request) -> str:
        raise BusinessException(
            "文章不存在", HttpCode.NOT_FOUND, ErrorCodes.ERROR_ARTICLE_NOT_FOUND
        )

    with pytest.raises(BusinessException) as error:
        asyncio.run(failing(request=_make_request()))

    assert error.value.status_code == HttpCode.NOT_FOUND
    assert error.value.error == ErrorCodes.ERROR_ARTICLE_NOT_FOUND
    queue_send.assert_not_awaited()


# 未知异常被包装为 503 服务不可用且不写入队列
def test_unexpected_error_is_wrapped_as_service_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    queue_send = _patch_dependencies(monkeypatch)

    @apiLog("未知异常")
    async def failing(request: Request) -> str:
        raise RuntimeError("boom")

    with pytest.raises(BusinessException) as error:
        asyncio.run(failing(request=_make_request()))

    assert error.value.status_code == HttpCode.SERVICE_UNAVAILABLE
    assert error.value.error.startswith("REQUEST_ERROR:")
    queue_send.assert_not_awaited()


# 流式响应在响应体全部消费完成后才记录日志
def test_streaming_response_is_tracked_until_stream_finishes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    queue_send = _patch_dependencies(monkeypatch)
    request = _make_request(method="GET", path="/ai/stream")

    async def chunks() -> AsyncGenerator[bytes, None]:
        yield b"first"
        yield b"second"

    @apiLog(ApiLogConfig("流式接口", include_params=False))
    async def stream(request: Request) -> StreamingResponse:
        return StreamingResponse(chunks(), media_type="text/plain")

    response = asyncio.run(stream(request=request))
    queue_send.assert_not_awaited()

    body_iterator = cast(AsyncIterator[bytes], response.body_iterator)

    async def consume() -> list[bytes]:
        return [chunk async for chunk in body_iterator]

    assert asyncio.run(consume()) == [b"first", b"second"]

    message = _queue_payload(queue_send)
    assert message["apiMethod"] == "GET"
    assert message["apiPath"] == "/ai/stream"


# 依赖注入参数被排除仅序列化请求体字段
def test_dependency_injections_are_excluded_from_queue_body() -> None:
    class _ArticleService:
        pass

    async def endpoint(
        db: Any = None,
        articleService: Any = None,
        body: _ArticlePayload | None = None,
    ) -> None:
        return None

    queue_body = api_log_module._extract_request_body_for_queue(
        endpoint,
        {
            "db": object(),
            "articleService": _ArticleService(),
            "body": _ArticlePayload(title="标题", phone="1"),
        },
        [],
    )

    assert queue_body == {"title": "标题", "phone": "1"}


# Query 注解的查询参数不进入队列请求体
def test_query_annotated_parameter_is_not_sent_to_queue() -> None:
    async def endpoint(
        page: Annotated[int, Query(ge=1)] = 1,
        body: _ArticlePayload | None = None,
    ) -> None:
        return None

    queue_body = api_log_module._extract_request_body_for_queue(
        endpoint, {"page": 2, "body": _ArticlePayload(title="标题", phone="1")}, []
    )

    assert queue_body == {"title": "标题", "phone": "1"}


# 上传文件序列化为描述文本而非二进制内容
def test_upload_file_content_is_not_serialized() -> None:
    serialized = api_log_module._serialize_for_json(
        {"avatar": _FakeUploadFile("photo.png"), "title": "标题"}
    )

    assert serialized == {
        "avatar": Messages.UPLOAD_FILE_DESCRIPTION("photo.png"),
        "title": "标题",
    }


# 路径参数值替换为占位符，无参数的路径保持不变
def test_normalize_path_with_params_replaces_values() -> None:
    request = _make_request(
        path="/article/1/comments/5", path_params={"id": "1", "comment_id": "5"}
    )

    assert (
        api_log_module._normalize_path_with_params("/article/1/comments/5", request)
        == "/article/:id/comments/:comment_id"
    )
    assert (
        api_log_module._normalize_path_with_params("/article/1", _make_request())
        == "/article/1"
    )
