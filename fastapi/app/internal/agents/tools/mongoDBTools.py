import json
from functools import lru_cache
from typing import Any, Optional

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from app.core.base import Logger
from app.core.constants import Messages, Prompts
from app.internal.clients import NestjsClient


class MongoDBTools:
    """MongoDB 日志查询工具集（通过 NestJS 内部接口远程查询）"""

    def __init__(self) -> None:
        """初始化 MongoDB 日志工具"""
        self.logger = Logger
        self._nestjs_client: NestjsClient = NestjsClient()

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

            # 确保 limit 是整数
            limit_int = int(limit)

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

    def get_langchain_tools(self) -> list[StructuredTool]:
        """获取 LangChain Tool 对象列表"""

        class EmptyInput(BaseModel):
            pass

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
                description=Messages.MONGODB_LIMIT_INPUT_DESC,
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
        ]


@lru_cache
def get_mongodb_tools() -> MongoDBTools:
    """获取 MongoDB 日志工具实例"""
    return MongoDBTools()
