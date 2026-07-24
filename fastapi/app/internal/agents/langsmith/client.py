import random
from contextlib import asynccontextmanager, contextmanager
from typing import Any, AsyncGenerator, Dict, Generator, Optional

from app.core.base import Logger
from app.core.constants import Messages
from langsmith import Client as LangSmithClient
from langsmith.run_trees import RunTree

from .config import LangSmithConfig, load_langsmith_config

_client: Optional[Any] = None
_config: Optional[LangSmithConfig] = None
_init_error: Optional[str] = None


def _is_tracing_enabled() -> bool:
    """检查追踪是否启用（含采样率判断）"""
    if _config is None or not _config.enabled:
        return False
    if _client is None:
        return False
    # 采样率判断
    if _config.sampling_rate >= 1.0:
        return True
    return random.random() < _config.sampling_rate


def init_langsmith(config: Optional[LangSmithConfig] = None) -> None:
    """初始化 LangSmith 客户端

    在应用启动时调用一次。初始化失败只记录日志，不抛出异常。

    Args:
        config: LangSmith 配置，不传则从环境变量自动加载
    """
    global _client, _config, _init_error

    if config is None:
        config = load_langsmith_config()
    _config = config

    if not config.enabled:
        Logger.info("LangSmith 追踪已关闭，跳过初始化")
        return

    if LangSmithClient is None:
        _init_error = "langsmith 包未安装，无法初始化"
        Logger.warning(_init_error)
        return

    try:
        _client = LangSmithClient(
            api_key=config.api_key,
            api_url=config.endpoint or "https://api.smith.langchain.com",
        )
        Logger.info(
            Messages.LANGSMITH_CLIENT_INITIALIZED(
                config.project, config.endpoint or "默认"
            )
        )
    except Exception as e:
        _init_error = Messages.LANGSMITH_CLIENT_INITIALIZATION_FAILED(e)
        _client = None
        Logger.warning(_init_error)


def shutdown_langsmith() -> None:
    """关闭 LangSmith 客户端，flush 缓冲区

    在应用关闭时调用。失败只记录日志。
    """
    global _client

    if _client is not None:
        try:
            # LangSmith client 通常不需要显式 flush，
            # 但为了完整性保留此接口
            Logger.info("LangSmith 客户端已关闭")
        except Exception as e:
            Logger.warning(Messages.LANGSMITH_CLIENT_CLOSE_FAILED(e))
    _client = None


def get_langsmith_client() -> Optional[Any]:
    """获取 LangSmith 客户端单例

    Returns:
        LangSmith Client 实例，追踪关闭或初始化失败时返回 None
    """
    if not _is_tracing_enabled():
        return None
    return _client


def get_langsmith_config() -> Optional[LangSmithConfig]:
    """获取当前 LangSmith 配置"""
    return _config


@contextmanager
def get_langsmith_context(
    name: str,
    tags: Optional[list] = None,
    metadata: Optional[Dict[str, Any]] = None,
    parent_run: Optional[Any] = None,
) -> Generator[Optional[Any], None, None]:
    """创建 LangSmith 根 Run 上下文管理器（同步版本）

    用于非 Runnable 边界的手工追踪，如 HTTP 根节点、同步任务。

    Args:
        name: Run 名称 (如 chat.send, chat.stream)
        tags: Tags 列表
        metadata: Metadata 字典（已脱敏）
        parent_run: 父 Run（用于子 Run）

    Yields:
        RunTree 实例，追踪关闭时返回 None
    """
    run: Optional[Any] = None
    client = get_langsmith_client()

    if client is None or RunTree is None:
        yield None
        return

    try:
        run = RunTree(
            name=name,
            run_type="chain",
            tags=tags,
            metadata=metadata,
            client=client,
        )
        if parent_run and hasattr(run, "parent_run"):
            run.parent_run = parent_run

        yield run
    except Exception as error:
        Logger.warning(Messages.LANGSMITH_RUN_CREATE_FAILED(error))
        yield None
    finally:
        if run is not None:
            try:
                run.end()
            except Exception as end_error:
                Logger.warning(Messages.LANGSMITH_RUN_END_FAILED(end_error))


@asynccontextmanager
async def get_langsmith_context_async(
    name: str,
    tags: Optional[list] = None,
    metadata: Optional[Dict[str, Any]] = None,
    parent_run: Optional[Any] = None,
) -> AsyncGenerator[Optional[Any], None]:
    """创建 LangSmith 根 Run 上下文管理器（异步版本）

    用于流式生成器的根 Trace，支持 SSE 完成、异常和断连收尾。

    Args:
        name: Run 名称 (如 chat.send, chat.stream)
        tags: Tags 列表
        metadata: Metadata 字典（已脱敏）
        parent_run: 父 Run

    Yields:
        RunTree 实例，追踪关闭时返回 None
    """
    run: Optional[Any] = None
    client = get_langsmith_client()

    if client is None or RunTree is None:
        yield None
        return

    try:
        run = RunTree(
            name=name,
            run_type="chain",
            tags=tags,
            metadata=metadata,
            client=client,
        )
        if parent_run and hasattr(run, "parent_run"):
            run.parent_run = parent_run

        yield run
    except Exception as error:
        Logger.warning(Messages.LANGSMITH_RUN_CREATE_FAILED(error))
        yield None
    finally:
        if run is not None:
            try:
                run.end()
            except Exception as end_error:
                Logger.warning(Messages.LANGSMITH_RUN_END_FAILED(end_error))
