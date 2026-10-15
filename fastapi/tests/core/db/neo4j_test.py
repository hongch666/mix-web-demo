import logging
from collections.abc import Iterator

import pytest
from neomodel.async_.query import _log_slow_query
from neomodel.config import get_config

from app.core.base import Logger
from app.core.db import (
    CypherDebugLogHandler,
    NEO4J_QUERY_LOGGER_NAMES,
    apply_cypher_debug_config,
    resolve_cypher_debug_config,
)


@pytest.fixture(autouse=True)
def _restore_cypher_debug_state() -> Iterator[None]:
    """恢复 neomodel 全局配置与 Cypher logger 状态，避免用例之间相互影响"""
    settings = get_config()
    original_enabled: bool = settings.cypher_debug
    original_slow_queries: float = settings.slow_queries
    original_loggers: dict[str, tuple[int, list[logging.Handler], bool]] = {
        name: (
            logging.getLogger(name).level,
            list(logging.getLogger(name).handlers),
            logging.getLogger(name).propagate,
        )
        for name in NEO4J_QUERY_LOGGER_NAMES
    }

    yield

    settings.cypher_debug = original_enabled
    settings.slow_queries = original_slow_queries
    for name, (level, handlers, propagate) in original_loggers.items():
        query_logger: logging.Logger = logging.getLogger(name)
        query_logger.setLevel(level)
        query_logger.handlers = handlers
        query_logger.propagate = propagate


# 配置段缺失、开关未声明或取值无法识别为真时保持关闭并采用 0 秒阈值
def test_resolve_cypher_debug_config_defaults_to_disabled() -> None:
    assert resolve_cypher_debug_config(None) == (False, 0.0)
    assert resolve_cypher_debug_config({}) == (False, 0.0)
    assert resolve_cypher_debug_config({"cypher_debug": False}) == (False, 0.0)


# 声明了开关与阈值时按声明取值，环境变量写入的字符串形式同样可识别
def test_resolve_cypher_debug_config_reads_declared_values() -> None:
    assert resolve_cypher_debug_config({"cypher_debug": True, "slow_queries": 1.5}) == (
        True,
        1.5,
    )
    assert resolve_cypher_debug_config({"cypher_debug": "true"}) == (True, 0.0)
    assert resolve_cypher_debug_config({"cypher_debug": "FALSE"}) == (False, 0.0)


# 阈值为负或无法转换为数字时回落到 0 秒，避免 neomodel 校验配置时抛错
def test_resolve_cypher_debug_config_sanitizes_threshold() -> None:
    assert resolve_cypher_debug_config({"cypher_debug": True, "slow_queries": -3}) == (
        True,
        0.0,
    )
    assert resolve_cypher_debug_config(
        {"cypher_debug": True, "slow_queries": "abc"}
    ) == (True, 0.0)


# 开启时同步 neomodel 开关并给两个 Cypher logger 挂上项目日志 handler
def test_apply_cypher_debug_config_enables_logging() -> None:
    apply_cypher_debug_config(True, 0.5)

    settings = get_config()
    assert settings.cypher_debug is True
    assert settings.slow_queries == 0.5
    for name in NEO4J_QUERY_LOGGER_NAMES:
        query_logger: logging.Logger = logging.getLogger(name)
        assert query_logger.level == logging.DEBUG
        assert query_logger.propagate is False
        assert any(
            isinstance(handler, CypherDebugLogHandler)
            for handler in query_logger.handlers
        )


# 关闭时同步关闭 neomodel 开关、摘掉 handler 并恢复默认传播行为
def test_apply_cypher_debug_config_disables_logging() -> None:
    apply_cypher_debug_config(True, 0.5)
    apply_cypher_debug_config(False)

    settings = get_config()
    assert settings.cypher_debug is False
    assert settings.slow_queries == 0.0
    for name in NEO4J_QUERY_LOGGER_NAMES:
        query_logger: logging.Logger = logging.getLogger(name)
        assert query_logger.level == logging.NOTSET
        assert query_logger.propagate is True
        assert not any(
            isinstance(handler, CypherDebugLogHandler)
            for handler in query_logger.handlers
        )


# 重复开启不会叠加 handler，避免同一条 Cypher 日志被输出多次
def test_apply_cypher_debug_config_is_idempotent() -> None:
    apply_cypher_debug_config(True)
    apply_cypher_debug_config(True)

    query_logger: logging.Logger = logging.getLogger("neomodel.async_.query")

    assert (
        sum(
            isinstance(handler, CypherDebugLogHandler)
            for handler in query_logger.handlers
        )
        == 1
    )


# 开启后 Cypher logger 的 DEBUG 记录经 handler 转交项目日志封装
def test_cypher_debug_log_is_forwarded_to_project_logger(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    forwarded: list[str] = []
    monkeypatch.setattr(Logger, "debug", forwarded.append)

    apply_cypher_debug_config(True)
    logging.getLogger("neomodel.async_.query").debug("query: MATCH (n) RETURN n")

    assert forwarded == ["query: MATCH (n) RETURN n"]


# 与 neomodel 的实际接线：开关打开后其内部慢查询日志能落到项目日志上
def test_neomodel_slow_query_log_reaches_project_logger(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    forwarded: list[str] = []
    monkeypatch.setattr(Logger, "debug", forwarded.append)

    apply_cypher_debug_config(True)
    _log_slow_query("MATCH (n) RETURN n", {"password": "unit-test-secret"}, 0.3)

    assert len(forwarded) == 1
    assert "MATCH (n) RETURN n" in forwarded[0]
    assert "unit-test-secret" not in forwarded[0]
