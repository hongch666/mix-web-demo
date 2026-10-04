from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ChangeEventDTO(BaseModel):
    """数据变更事件，与 Spring 下发的精确同步事件结构对应"""

    resource: str = Field(default="", description="资源名，如 articles、comments")
    change_type: str = Field(default="", description="变更类型：insert、update、delete")
    ids: list[int] = Field(default_factory=list, description="受影响的主键集合")
    action: str = Field(default="", description="原始操作类型")
    trigger_user_id: Optional[int] = Field(default=None, description="触发变更的用户ID")
    trigger_username: Optional[str] = Field(
        default=None, description="触发变更的用户名"
    )
    occurred_at: Optional[str] = Field(default=None, description="事件产生时间")


class VectorSyncDTO(BaseModel):
    """向量同步请求，携带变更类型与文章主键"""

    resource: str = Field(default="articles", description="资源名，固定 articles")
    change_type: str = Field(default="", description="变更类型：insert、update、delete")
    ids: list[int] = Field(default_factory=list, description="受影响文章ID")
    trigger_user_id: Optional[int] = Field(default=None, description="触发变更的用户ID")
    occurred_at: Optional[str] = Field(default=None, description="事件产生时间")


class Neo4jSyncDTO(BaseModel):
    """Neo4j 精确同步请求，携带一批变更事件"""

    events: list[ChangeEventDTO] = Field(
        default_factory=list, description="变更事件列表"
    )
    force_full: bool = Field(default=False, description="是否全量同步（含清理）")


class WarehouseSyncDTO(BaseModel):
    """数仓同步请求，按资源名精确定位需要刷新的源表"""

    resources: list[str] = Field(
        default_factory=list, description="本次变更涉及的源表资源名，为空时全表同步"
    )
