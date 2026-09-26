"""LangSmith tags 与 metadata 构造的单元测试"""

from app.internal.agents.langsmith.tags import build_chat_metadata, build_chat_tags


# 基础 tag 包含环境、路由、模型、模式与服务维度
def test_build_chat_tags_includes_base_dimensions() -> None:
    tags = build_chat_tags("prod", "chat_send", "gpt", "agent")

    assert tags == [
        "env:prod",
        "route:chat_send",
        "model:gpt",
        "mode:agent",
        "service:fastapi",
    ]


# 开启流式与 RAG 时追加 feature tag、自定义 tag 置于末尾
def test_build_chat_tags_appends_feature_flags_and_extra() -> None:
    tags = build_chat_tags(
        "dev",
        "chat_stream",
        "glm",
        "direct",
        streaming=True,
        rag_enabled=True,
        extra_tags=["tenant:1"],
    )

    assert "streaming:true" in tags
    assert "feature:rag" in tags
    assert tags[-1] == "tenant:1"


# metadata 对用户哈希、会话 ID 截断并保留意图等字段
def test_build_chat_metadata_hashes_user_and_truncates_conversation() -> None:
    metadata = build_chat_metadata(
        request_id="req-1",
        user_id="1001",
        conversation_id="c" * 100,
        model_provider="gpt",
        model_name="gpt-4",
        streaming=True,
        agent_mode=True,
        rag_enabled=True,
        intent="article_search",
        intent_resolution="structured",
        deployment_env="test",
        release_version="v1",
    )

    assert metadata is not None
    assert metadata["request_id"] == "req-1"
    assert metadata["user_hash"].startswith("u_")
    assert "1001" not in metadata["user_hash"]
    assert len(metadata["conversation_id"]) == 64
    assert metadata["intent"] == "article_search"
    assert metadata["intent_resolution"] == "structured"
    assert metadata["release_version"] == "v1"
    assert metadata["streaming"] is True
    assert metadata["agent_mode"] is True


# 可选字段缺省时省略 intent 等键且用户哈希为 anonymous
def test_build_chat_metadata_omits_optional_fields_when_absent() -> None:
    metadata = build_chat_metadata(
        request_id="req-2",
        user_id="",
        conversation_id="",
        model_provider="gpt",
        model_name="gpt-4",
    )

    assert metadata is not None
    assert metadata["conversation_id"] == ""
    assert "intent" not in metadata
    assert "release_version" not in metadata
    assert metadata["user_hash"] == "anonymous"


# 额外 metadata 中的敏感字段经脱敏后合并
def test_build_chat_metadata_sanitizes_extra_metadata() -> None:
    metadata = build_chat_metadata(
        request_id="req-3",
        user_id="1001",
        conversation_id="conv",
        model_provider="gpt",
        model_name="gpt-4",
        extra_metadata={"api_key": "unit-test-value", "note": "ok"},
    )

    assert metadata is not None
    assert metadata["api_key"] == "***已脱敏***"
    assert metadata["note"] == "ok"
