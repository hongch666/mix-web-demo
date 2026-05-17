import json
from functools import lru_cache
from typing import Any, Dict, List, Optional

from app.core.base import Constants, Logger
from app.internal.clients import NestjsClient
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field


class MongoDBTools:
    """MongoDB 日志查询工具集"""

    def __init__(self) -> None:
        self.client = NestjsClient()
        self.logger = Logger

    async def list_mongodb_collections(self) -> str:
        try:
            data = await self.client.list_log_collections()
            return self._format_results(data.get("collections", []))
        except Exception as e:
            error_msg = f"{Constants.MONGODB_TOOL_COLLECTION_FETCH_ERROR}: {str(e)}"
            self.logger.error(error_msg)
            return error_msg

    async def query_mongodb(
        self,
        collection: str,
        filter_dict: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        sort: Optional[Dict[str, int]] = None,
    ) -> str:
        try:
            if not collection:
                return Constants.COLLECTION_NAME_VALIDATION_ERROR
            data = await self.client.query_log(
                collection=collection,
                filter_dict=filter_dict or {},
                limit=limit,
                sort=sort or {"createdAt": -1},
            )
            return self._format_results(data)
        except Exception as e:
            error_msg = f"{Constants.MONGODB_TOOL_QUERY_ERROR}: {str(e)}"
            self.logger.error(error_msg)
            return error_msg

    async def search_log_keywords(self) -> str:
        try:
            return self._format_results(await self.client.get_search_keywords())
        except Exception as e:
            return f"{Constants.SEARCH_LOG_KEYWORDS_ERROR}: {str(e)}"

    async def user_view_distribution(self, user_id: int) -> str:
        try:
            return self._format_results(await self.client.get_view_distribution(user_id))
        except Exception as e:
            return f"{Constants.USER_VIEW_DISTRIBUTION_ERROR}: {str(e)}"

    async def api_average_speed(self) -> str:
        try:
            return self._format_results(await self.client.get_api_average_speed())
        except Exception as e:
            return f"{Constants.API_AVERAGE_SPEED_ERROR}: {str(e)}"

    async def api_called_count(self) -> str:
        try:
            return self._format_results(await self.client.get_called_count_apis())
        except Exception as e:
            return f"{Constants.API_CALLED_COUNT_ERROR}: {str(e)}"

    def get_langchain_tools(self) -> List[StructuredTool]:
        class EmptyInput(BaseModel):
            pass

        class QueryMongoDBInput(BaseModel):
            collection: str = Field(
                description=Constants.MONGODB_COLLECTION_NAME_INPUT_DESC
            )
            filter_dict: Dict[str, Any] = Field(
                default_factory=dict,
                description=Constants.MONGODB_FILTER_INPUT_DESC,
            )
            limit: int = Field(
                default=10,
                ge=1,
                le=100,
                description=Constants.MONGODB_LIMIT_INPUT_DESC,
            )
            sort: Dict[str, int] = Field(
                default_factory=lambda: {"createdAt": -1},
                description=Constants.MONGODB_SORT_INPUT_DESC,
            )

        class UserViewDistributionInput(BaseModel):
            user_id: int = Field(description=Constants.USER_ID_INPUT_DESC)

        return [
            StructuredTool(
                name=Constants.MONGODB_LIST_COLLECTIONS_TOOL_NAME,
                description=Constants.MONGODB_LIST_COLLECTIONS_TOOL_DESC,
                coroutine=self.list_mongodb_collections,
                args_schema=EmptyInput,
            ),
            StructuredTool(
                name=Constants.MONGODB_QUERY_TOOL_NAME,
                description=Constants.MONGODB_QUERY_TOOL_DESC,
                coroutine=self.query_mongodb,
                args_schema=QueryMongoDBInput,
            ),
            StructuredTool(
                name=Constants.SEARCH_LOG_KEYWORDS_TOOL_NAME,
                description=Constants.SEARCH_LOG_KEYWORDS_TOOL_DESC,
                coroutine=self.search_log_keywords,
                args_schema=EmptyInput,
            ),
            StructuredTool(
                name=Constants.USER_VIEW_DISTRIBUTION_TOOL_NAME,
                description=Constants.USER_VIEW_DISTRIBUTION_TOOL_DESC,
                coroutine=self.user_view_distribution,
                args_schema=UserViewDistributionInput,
            ),
            StructuredTool(
                name=Constants.API_AVERAGE_SPEED_TOOL_NAME,
                description=Constants.API_AVERAGE_SPEED_TOOL_DESC,
                coroutine=self.api_average_speed,
                args_schema=EmptyInput,
            ),
            StructuredTool(
                name=Constants.API_CALLED_COUNT_TOOL_NAME,
                description=Constants.API_CALLED_COUNT_TOOL_DESC,
                coroutine=self.api_called_count,
                args_schema=EmptyInput,
            ),
        ]

    def _format_results(self, results: Any) -> str:
        try:
            return json.dumps(results, ensure_ascii=False, indent=2)
        except Exception:
            return str(results)


@lru_cache
def get_mongodb_tools() -> MongoDBTools:
    return MongoDBTools()
