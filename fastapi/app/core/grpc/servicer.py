import json
from typing import Any

from app.core.base import Logger
from app.core.constants import Messages
from app.internal.schemas import GraphSearchEnhanceReq, VectorSearchEnhanceReq
from app.internal.services import (
    AlgorithmService,
    GraphSearchService,
    VectorSearchService,
    AiHistoryService,
    get_ai_history_service,
)
from app.proto.fastapi import ai_history_pb2_grpc, algorithm_pb2_grpc, search_enhance_pb2_grpc
from app.proto.common import result_pb2


def _result(
    data: Any,
    code: int = 200,
    message: str = Messages.GRPC_RESULT_SUCCESS,
) -> result_pb2.Result:
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return result_pb2.Result(code=code, message=message, data=payload)


class SearchEnhanceServicer(search_enhance_pb2_grpc.SearchEnhanceServicer):
    """gRPC 协议适配层，只负责协议转换并委托现有 Service。"""

    def __init__(
        self,
        graph_service: GraphSearchService,
        vector_service: VectorSearchService,
    ) -> None:
        self._graph_service = graph_service
        self._vector_service = vector_service

    async def EnhanceGraph(self, request: Any, context: Any) -> result_pb2.Result:
        result = await self._graph_service.enhance(
            GraphSearchEnhanceReq(
                userId=request.user_id or None,
                keyword=request.keyword,
                articleIds=list(request.article_ids),
                categoryName=request.category_name,
                subCategoryName=request.sub_category_name,
                tags=list(request.tags),
                limit=request.limit,
                mode=request.mode,
            )
        )
        Logger.info(Messages.GRPC_REQUEST_HANDLED("EnhanceGraph"))
        return _result(result.model_dump(by_alias=True))

    async def EnhanceVector(self, request: Any, context: Any) -> result_pb2.Result:
        result = await self._vector_service.enhance(
            VectorSearchEnhanceReq(
                userId=request.user_id or None,
                keyword=request.keyword,
                articleIds=list(request.article_ids),
                categoryName=request.category_name,
                subCategoryName=request.sub_category_name,
                tags=list(request.tags),
                limit=request.limit,
                topK=request.top_k,
                mode=request.mode,
            )
        )
        Logger.info(Messages.GRPC_REQUEST_HANDLED("EnhanceVector"))
        return _result(result.model_dump(by_alias=True))


class AlgorithmServicer(algorithm_pb2_grpc.AlgorithmServicer):
    """搜索算法 gRPC 协议适配层。"""

    def __init__(self, algorithm_service: AlgorithmService) -> None:
        self._algorithm_service = algorithm_service

    async def GetSearchWeights(self, request: Any, context: Any) -> result_pb2.Result:
        Logger.info(Messages.GRPC_REQUEST_HANDLED("GetSearchWeights"))
        return _result(self._algorithm_service.get_weights())

    async def GetSearchScript(self, request: Any, context: Any) -> result_pb2.Result:
        Logger.info(Messages.GRPC_REQUEST_HANDLED("GetSearchScript"))
        return _result(self._algorithm_service.get_es_script())

    async def GetSearchScriptParams(self, request: Any, context: Any) -> result_pb2.Result:
        Logger.info(Messages.GRPC_REQUEST_HANDLED("GetSearchScriptParams"))
        return _result(self._algorithm_service.get_script_params())


class AiHistoryServicer(ai_history_pb2_grpc.AiHistoryServicer):
    """AI 历史内部读写 gRPC 适配层，复用现有 Mapper 和事务。"""

    def __init__(self, ai_history_service: AiHistoryService) -> None:
        self._ai_history_service = ai_history_service

    @staticmethod
    def _payload(request: Any) -> dict[str, Any]:
        if not request.payload:
            return {}
        value = json.loads(request.payload.decode("utf-8"))
        return value if isinstance(value, dict) else {}

    async def _db_call(self, operation: Any, payload: dict[str, Any]) -> result_pb2.Result:
        from app.core.db.mysql import get_db

        db_generator = get_db()
        db = await anext(db_generator)
        try:
            return _result(await operation(db, payload))
        finally:
            await db_generator.aclose()

    async def Get(self, request: Any, context: Any) -> result_pb2.Result:
        payload = self._payload(request)
        return await self._db_call(
            lambda db, item: self._ai_history_service.get_ai_history_by_id(
                int(item.get("path", {}).get("id", 0)), db
            ),
            payload,
        )

    async def Update(self, request: Any, context: Any) -> result_pb2.Result:
        payload = self._payload(request)
        return await self._db_call(
            lambda db, item: self._ai_history_service.update_ai_history(
                int(item.get("path", {}).get("id", 0)), item.get("body", {}), db
            ),
            payload,
        )

    async def Delete(self, request: Any, context: Any) -> result_pb2.Result:
        payload = self._payload(request)
        return await self._db_call(
            lambda db, item: self._ai_history_service.delete_ai_history_by_id(
                int(item.get("path", {}).get("id", 0)), db
            ),
            payload,
        )
