from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any, Optional

from app.core.base import Logger
from app.core.constants import Messages


@dataclass(frozen=True)
class ToolScope:
    """Agent 工具的请求级行权限作用域"""

    user_id: int
    is_admin: bool


_current_tool_scope: ContextVar[Optional[ToolScope]] = ContextVar(
    "current_tool_scope", default=None
)

def set_tool_scope(user_id: int, is_admin: bool) -> None:
    """写入当前请求的工具作用域，请求内后续执行的工具都读取该作用域"""
    _current_tool_scope.set(ToolScope(user_id=user_id, is_admin=is_admin))


def get_tool_scope() -> Optional[ToolScope]:
    """读取当前请求的工具作用域，未设置时返回 None"""
    return _current_tool_scope.get()


def clear_tool_scope() -> None:
    """清除当前请求的工具作用域"""
    _current_tool_scope.set(None)


def enforce_sql_row_scope(query: str, params: Optional[dict[str, Any]]) -> Optional[str]:
    """SQL 工具的行级范围校验，返回拒绝消息或 None 表示放行

    管理员放行；未登录或作用域缺失一律拒绝（fail-closed）。
    任意 SQL 无法通过字符串匹配可靠地证明行级隔离，因此非管理员禁止使用。
    """
    scope = get_tool_scope()
    if scope is None:
        return Messages.SQL_TOOL_SCOPE_MISSING

    if scope.is_admin:
        return None

    return Messages.NON_ADMIN_ARBITRARY_QUERY_FORBIDDEN


def enforce_mongodb_row_scope(filter_dict: Optional[dict[str, Any]]) -> Optional[str]:
    """MongoDB 日志工具的行级范围校验，返回拒绝消息或 None 表示放行

    MongoDB 过滤器支持逻辑运算符和嵌套结构，无法通过顶层字段检查可靠地证明行级隔离，因此非管理员禁止使用
    """
    scope = get_tool_scope()
    if scope is None:
        return Messages.SQL_TOOL_SCOPE_MISSING

    if scope.is_admin:
        return None

    return Messages.NON_ADMIN_ARBITRARY_QUERY_FORBIDDEN


def log_scope_denial(tool_name: str, denial: str) -> None:
    """记录一次行级范围拒绝，便于审计"""
    Logger.warning(f"[工具权限] {tool_name} 拒绝执行: {denial}")
