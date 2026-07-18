from typing import Any, Dict, List, Optional

from .sanitizer import sanitize_metadata, sanitize_user_id


def build_chat_tags(
    env: str,
    route: str,
    model_provider: str,
    mode: str,
    streaming: bool = False,
    rag_enabled: bool = False,
    extra_tags: Optional[List[str]] = None,
) -> List[str]:
    """构建聊天请求的 LangSmith tags

    Args:
        env: 部署环境标识 (dev/test/prod)
        route: 路由标识 (chat_send/chat_stream)
        model_provider: 模型提供商 (gpt/gemini/deepseek)
        mode: 对话模式 (agent/direct)
        streaming: 是否流式
        rag_enabled: 是否启用 RAG
        extra_tags: 额外标签列表

    Returns:
        标准化 tags 列表
    """
    tags = [
        f"env:{env}",
        f"route:{route}",
        f"model:{model_provider}",
        f"mode:{mode}",
        "service:fastapi",
    ]
    if streaming:
        tags.append("streaming:true")
    if rag_enabled:
        tags.append("feature:rag")
    if extra_tags:
        tags.extend(extra_tags)
    return tags


def build_chat_metadata(
    request_id: str,
    user_id: str,
    conversation_id: str,
    model_provider: str,
    model_name: str,
    streaming: bool = False,
    agent_mode: bool = False,
    rag_enabled: bool = False,
    intent: Optional[str] = None,
    intent_resolution: Optional[str] = None,
    deployment_env: str = "dev",
    release_version: Optional[str] = None,
    extra_metadata: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """构建聊天请求的 LangSmith metadata

    返回的 metadata 已通过脱敏器处理，不包含原始用户 ID、对话内容等敏感信息。
    """
    metadata: Dict[str, Any] = {
        "request_id": request_id,
        "user_hash": sanitize_user_id(user_id),
        "conversation_id": conversation_id[:64] if conversation_id else "",
        "service": "fastapi",
        "model_provider": model_provider,
        "model_name": model_name,
        "streaming": streaming,
        "agent_mode": agent_mode,
        "rag_enabled": rag_enabled,
        "deployment_env": deployment_env,
    }

    if intent:
        metadata["intent"] = intent
    if intent_resolution:
        metadata["intent_resolution"] = intent_resolution
    if release_version:
        metadata["release_version"] = release_version
    if extra_metadata:
        metadata.update(extra_metadata)

    return sanitize_metadata(metadata)
