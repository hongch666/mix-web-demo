from fastapi import FastAPI
from fastapi.testclient import TestClient
from opentelemetry import context, trace
from opentelemetry.trace import NonRecordingSpan, SpanContext, TraceFlags, TraceState

from app.common.middleware.contextMiddleware import (
    ContextMiddleware,
    _extract_bearer_token,
    get_current_internal_token,
    get_current_trace_id,
    get_current_user_id,
    get_current_username,
)


def test_extract_bearer_token_accepts_only_bearer_scheme() -> None:
    assert _extract_bearer_token("Bearer abc") == "abc"
    assert _extract_bearer_token("Basic abc") is None
    assert _extract_bearer_token("Bearer ") == ""
    assert _extract_bearer_token(None) is None


def test_context_middleware_populates_headers_and_resets_after_request() -> None:
    app = FastAPI()
    app.add_middleware(ContextMiddleware)

    @app.get("/context")
    async def context_values() -> dict[str, object]:
        return {
            "user_id": get_current_user_id(),
            "username": get_current_username(),
            "internal_token": get_current_internal_token(),
        }

    with TestClient(app) as client:
        response = client.get(
            "/context",
            headers={
                "X-User-Id": "42",
                "X-Username": "alice",
                "X-Internal-Token": "Bearer internal.jwt",
            },
        )

    assert response.status_code == 200
    assert response.json() == {
        "user_id": 42,
        "username": "alice",
        "internal_token": "internal.jwt",
    }
    assert get_current_user_id() is None
    assert get_current_username() is None
    assert get_current_internal_token() is None


def test_context_middleware_handles_invalid_user_id() -> None:
    app = FastAPI()
    app.add_middleware(ContextMiddleware)

    @app.get("/")
    async def context_value() -> dict[str, object]:
        return {"user_id": get_current_user_id()}

    response = TestClient(app).get("/", headers={"X-User-Id": "not-a-number"})

    assert response.status_code == 200
    assert response.json() == {"user_id": None}


def test_get_current_trace_id_returns_active_span_trace_id() -> None:
    trace_id = 0x0123456789ABCDEF0123456789ABCDEF
    span_context = SpanContext(
        trace_id=trace_id,
        span_id=0x0123456789ABCDEF,
        is_remote=False,
        trace_flags=TraceFlags(TraceFlags.SAMPLED),
        trace_state=TraceState(),
    )
    token = context.attach(
        trace.set_span_in_context(NonRecordingSpan(span_context))
    )
    try:
        assert get_current_trace_id() == format(trace_id, "032x")
    finally:
        context.detach(token)
