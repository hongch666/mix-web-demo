import re
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

# SQL 中 user_id 列与绑定参数名的匹配模式
SQL_USER_ID_COLUMN_REGEX = re.compile(r"\buser_id\b", re.IGNORECASE)
SQL_USER_ID_PARAM_KEY_REGEX = re.compile(r"user_?id", re.IGNORECASE)
SQL_USER_ID_LITERAL_REGEX = re.compile(r"\buser_id\s*(?:=|==)\s*(\d+)", re.IGNORECASE)


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

    admin 放行；未登录或作用域缺失一律拒绝（fail-closed）；
    非 admin 要求查询包含 user_id 条件且绑定值等于当前用户
    """
    scope = get_tool_scope()
    if scope is None:
        return Messages.SQL_TOOL_SCOPE_MISSING

    if scope.is_admin:
        return None

    if not query or not SQL_USER_ID_COLUMN_REGEX.search(query):
        return Messages.SQL_TOOL_ROW_SCOPE_REQUIRED(scope.user_id)

    bound_values = _extract_bound_user_ids(params)
    if bound_values:
        for value in bound_values:
            if value != scope.user_id:
                return Messages.SQL_TOOL_ROW_SCOPE_FOREIGN_USER(scope.user_id)
        return None

    literal_match = SQL_USER_ID_LITERAL_REGEX.search(query)
    if literal_match and int(literal_match.group(1)) != scope.user_id:
        return Messages.SQL_TOOL_ROW_SCOPE_FOREIGN_USER(scope.user_id)
    if not literal_match:
        return Messages.SQL_TOOL_ROW_SCOPE_REQUIRED(scope.user_id)

    return None


def enforce_mongodb_row_scope(filter_dict: Optional[dict[str, Any]]) -> Optional[str]:
    """MongoDB 日志工具的行级范围校验，返回拒绝消息或 None 表示放行

    非 admin 要求 filter 中包含 userId/user_id 且等于当前用户
    """
    scope = get_tool_scope()
    if scope is None:
        return Messages.SQL_TOOL_SCOPE_MISSING

    if scope.is_admin:
        return None

    filter_dict = filter_dict or {}
    for key in ("userId", "user_id"):
        if key in filter_dict:
            value = _to_int(filter_dict[key])
            if value is None or value != scope.user_id:
                return Messages.SQL_TOOL_ROW_SCOPE_FOREIGN_USER(scope.user_id)
            return None

    return Messages.MONGODB_ROW_SCOPE_REQUIRED(scope.user_id)


def _extract_bound_user_ids(params: Optional[dict[str, Any]]) -> list[int]:
    """从绑定参数中提取 user_id 类键的值"""
    if not params:
        return []
    values: list[int] = []
    for key, value in params.items():
        if SQL_USER_ID_PARAM_KEY_REGEX.search(str(key)):
            parsed = _to_int(value)
            if parsed is not None:
                values.append(parsed)
    return values


def _to_int(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def log_scope_denial(tool_name: str, denial: str) -> None:
    """记录一次行级范围拒绝，便于审计"""
    Logger.warning(f"[工具权限] {tool_name} 拒绝执行: {denial}")
