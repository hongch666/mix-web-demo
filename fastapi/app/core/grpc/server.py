from typing import Optional

import grpc
from app.core.base import Logger
from app.core.config import load_config
from app.core.constants import Messages
from app.internal.services import (
    get_ai_history_service,
    get_algorithm_service,
    get_graph_search_service,
    get_vector_search_service,
)
from app.proto.fastapi import ai_history_pb2_grpc, algorithm_pb2_grpc, search_enhance_pb2_grpc

from .interceptors import InternalTokenInterceptor, UserContextInterceptor
from .servicer import AiHistoryServicer, AlgorithmServicer, SearchEnhanceServicer


class GrpcServerManager:
    """与 Uvicorn 共用 asyncio 事件循环的 gRPC 服务生命周期管理器。"""

    def __init__(self, port: int, enabled: bool = True) -> None:
        self._port = port
        self._enabled = enabled
        self._server: Optional[grpc.aio.Server] = None

    async def start(self) -> None:
        if not self._enabled:
            Logger.info(Messages.GRPC_SERVER_DISABLED)
            return
        self._server = grpc.aio.server(
            interceptors=[UserContextInterceptor(), InternalTokenInterceptor()]
        )
        search_enhance_pb2_grpc.add_SearchEnhanceServicer_to_server(
            SearchEnhanceServicer(
                get_graph_search_service(),
                get_vector_search_service(),
            ),
            self._server,
        )
        algorithm_pb2_grpc.add_AlgorithmServicer_to_server(
            AlgorithmServicer(get_algorithm_service()),
            self._server,
        )
        ai_history_pb2_grpc.add_AiHistoryServicer_to_server(
            AiHistoryServicer(get_ai_history_service()),
            self._server,
        )
        bind_result = self._server.add_insecure_port(f"[::]:{self._port}")
        if bind_result == 0:
            raise RuntimeError(Messages.GRPC_SERVER_BIND_FAILED(self._port))
        await self._server.start()
        Logger.info(Messages.GRPC_SERVER_STARTED(self._port))

    async def stop(self) -> None:
        if self._server is not None:
            await self._server.stop(grace=5)
            self._server = None
            Logger.info(Messages.GRPC_SERVER_STOPPED)


def create_grpc_server_manager() -> GrpcServerManager:
    config = load_config("grpc")
    return GrpcServerManager(int(config["port"]), bool(config.get("enabled", True)))
