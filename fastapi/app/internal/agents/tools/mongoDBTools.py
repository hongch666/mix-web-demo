import json
from functools import lru_cache
from typing import Any, Optional

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from app.core.base import Logger
from app.core.constants import Defaults, Messages, Prompts
from app.internal.agents.toolScope import enforce_mongodb_row_scope, log_scope_denial
from app.internal.clients import NestjsClient, get_nestjs_client


class MongoDBTools:
    """MongoDB 日志查询工具集（通过 NestJS 内部接口远程查询）"""

    def __init__(self, nestjs_client: NestjsClient) -> None:
        """初始化 MongoDB 日志工具"""
        self.logger = Logger
        self._nestjs_client: NestjsClient = nestjs_client

    async def list_mongodb_collections(self) -> str:
        """列出 MongoDB 数据库中的所有 collection 及其基本信息"""
        try:
            collections_info: list[
                dict[str, Any]
            ] = await self._nestjs_client.list_mongodb_collections()
            return json.dumps(collections_info, ensure_ascii=False, indent=2)
        except Exception as e:
            error_msg = Messages.MONGODB_COLLECTION_LIST_FAILED(e)
            self.logger.error(error_msg)
            return error_msg

    async def query_mongodb(
        self,
        collection_name: str,
        filter_dict: Optional[dict[str, Any]] = None,
        limit: int = 10,
    ) -> str:
        """通用的 MongoDB 查询工具，可以查询任意 collection"""
        try:
            # 验证必需参数
            if not collection_name:
                return Messages.COLLECTION_NAME_VALIDATION_ERROR

            # 行级范围校验：非 admin 仅允许查询本人日志
            denial = enforce_mongodb_row_scope(filter_dict)
            if denial:
                log_scope_denial("MongoDBTools", denial)
                return denial

            # limit 收敛到 NestJS 接口接受的区间：超限会被其校验管道拒绝
            limit_int = min(max(int(limit), 1), Defaults.MONGODB_QUERY_MAX_LIMIT)

            results: list[dict[str, Any]] = await self._nestjs_client.query_mongodb(
                collection_name, filter_dict, limit_int
            )

            self.logger.info(
                Messages.MONGODB_QUERY_RESULT(
                    collection_name, filter_dict or {}, len(results)
                )
            )
            return json.dumps(results, ensure_ascii=False, indent=2)

        except Exception as e:
            error_msg = Messages.MONGODB_QUERY_FAILED(e)
            self.logger.error(error_msg)
            return error_msg

    async def aggregate_mongodb(
        self,
        collection_name: str,
        pipeline: list[dict[str, Any]],
        limit: int = 20,
    ) -> str:
        """受限聚合查询工具，支持分组、排序、计数等日志统计场景"""
        try:
            if not collection_name:
                return Messages.COLLECTION_NAME_VALIDATION_ERROR
            if not pipeline:
                return Messages.MONGODB_PIPELINE_EMPTY_ERROR

            # 与 find 查询同一行级规则：过滤器无法证明行级隔离，非管理员一律拒绝
            denial = enforce_mongodb_row_scope(None)
            if denial:
                log_scope_denial("MongoDBTools", denial)
                return denial

            # limit 收敛到 NestJS 接口接受的区间：超限会被其校验管道拒绝
            limit_int = min(max(int(limit), 1), Defaults.MONGODB_AGGREGATE_MAX_DOCS)

            results: list[dict[str, Any]] = await self._nestjs_client.aggregate_mongodb(
                collection_name, pipeline, limit_int
            )

            self.logger.info(
                Messages.MONGODB_QUERY_RESULT(collection_name, pipeline, len(results))
            )
            return json.dumps(results, ensure_ascii=False, indent=2)

        except Exception as e:
            error_msg = Messages.MONGODB_AGGREGATE_FAILED(e)
            self.logger.error(error_msg)
            return error_msg

    def get_langchain_tools(self) -> list[StructuredTool]:
        """获取 LangChain Tool 对象列表"""

        class EmptyInput(BaseModel):
            pass

        class AggregateMongoInput(BaseModel):
            collection_name: str = Field(
                description=Messages.MONGODB_COLLECTION_NAME_INPUT_DESC
            )
            pipeline: list[dict[str, Any]] = Field(
                description=Messages.MONGODB_PIPELINE_INPUT_DESC
            )
            limit: int = Field(
                default=20,
                ge=1,
                le=Defaults.MONGODB_AGGREGATE_MAX_DOCS,
                description=Messages.MONGODB_AGGREGATE_LIMIT_INPUT_DESC(
                    Defaults.MONGODB_AGGREGATE_MAX_DOCS
                ),
            )

        class QueryMongoInput(BaseModel):
            collection_name: str = Field(
                description=Messages.MONGODB_COLLECTION_NAME_INPUT_DESC
            )
            filter_dict: dict[str, Any] = Field(
                default_factory=dict,
                description=Messages.MONGODB_FILTER_INPUT_DESC,
            )
            limit: int = Field(
                default=10,
                ge=1,
                le=Defaults.MONGODB_QUERY_MAX_LIMIT,
                description=Messages.MONGODB_LIMIT_INPUT_DESC(
                    Defaults.MONGODB_QUERY_MAX_LIMIT
                ),
            )

        return [
            StructuredTool(
                name=Messages.MONGODB_LIST_COLLECTIONS_TOOL_NAME,
                description=Prompts.MONGODB_LIST_COLLECTIONS_TOOL_DESC,
                coroutine=self.list_mongodb_collections,
                args_schema=EmptyInput,
            ),
            StructuredTool(
                name=Messages.MONGODB_QUERY_TOOL_NAME,
                description=Prompts.MONGODB_QUERY_TOOL_DESC,
                coroutine=self.query_mongodb,
                args_schema=QueryMongoInput,
            ),
            StructuredTool(
                name=Messages.MONGODB_AGGREGATE_TOOL_NAME,
                description=Prompts.MONGODB_AGGREGATE_TOOL_DESC,
                coroutine=self.aggregate_mongodb,
                args_schema=AggregateMongoInput,
            ),
        ]


@lru_cache
def get_mongodb_tools(nestjs_client: Optional[NestjsClient] = None) -> MongoDBTools:
    """获取 MongoDB 日志工具实例"""
    return MongoDBTools(nestjs_client or get_nestjs_client())
