"""FastAPI 远程调用的 gRPC 通道。

请求体使用 common.v1.JsonRequest 承载原 HTTP 调用的 method/path/query/body，
保证迁移期间业务客户端签名不变；协议错误只交给 HTTP 层兜底。
"""

import json
import re
from typing import Any, Awaitable, Callable, Dict, Optional, Tuple

import grpc
from app.core.constants import HttpCode, Messages
from app.core.errors import BusinessException
from app.core.base import Logger
from app.proto.common import result_pb2
from app.proto.nestjs import log_pb2_grpc
from app.proto.spring import (
    article_pb2_grpc,
    category_pb2_grpc,
    interaction_pb2_grpc,
    statistics_pb2_grpc,
    user_pb2_grpc,
)

from .nacos import get_service_instance

GrpcInvoker = Callable[[Any, result_pb2.JsonRequest], Awaitable[result_pb2.Result]]


def _match_rpc(service_name: str, path: str) -> Optional[Tuple[Any, str]]:
    if service_name == "spring":
        # 文件流接口属于长期 HTTP，不能被统计接口的通配规则捕获。
        if path == "/articles/statistics/excel-export":
            return None
        routes = (
            (r"^/articles/list$", article_pb2_grpc.ArticleStub, "List"),
            (r"^/articles/batch$", article_pb2_grpc.ArticleStub, "Batch"),
            (r"^/articles/views/batch$", article_pb2_grpc.ArticleStub, "ViewsBatch"),
            (r"^/articles/by-title$", article_pb2_grpc.ArticleStub, "ByTitle"),
            (r"^/articles/[^/]+$", article_pb2_grpc.ArticleStub, "Get"),
            (r"^/articles/user/[^/]+$", article_pb2_grpc.ArticleStub, "UserArticles"),
            (r"^/category/batch$", category_pb2_grpc.CategoryStub, "Batch"),
            (r"^/category/sub/batch$", category_pb2_grpc.CategoryStub, "SubBatch"),
            (r"^/category/internal/all$", category_pb2_grpc.CategoryStub, "All"),
            (r"^/category/internal/sub/with-parent$", category_pb2_grpc.CategoryStub, "SubWithParent"),
            (r"^/category/reference/sub/[^/]+$", category_pb2_grpc.CategoryStub, "ReferenceSub"),
            (r"^/users/[0-9]+$", user_pb2_grpc.UserStub, "Get"),
            (r"^/users/batch$", user_pb2_grpc.UserStub, "Batch"),
            (r"^/users/by-name$", user_pb2_grpc.UserStub, "ByName"),
            (r"^/users/by-github-id/[^/]+$", user_pb2_grpc.UserStub, "ByGithubId"),
            (r"^/users/github-user$", user_pb2_grpc.UserStub, "GithubUser"),
            (r"^/users/[^/]+/is-admin$", user_pb2_grpc.UserStub, "IsAdmin"),
            (r"^/users/github/token-ticket$", user_pb2_grpc.UserStub, "TokenTicket"),
            (r"^/comments/scores/batch$", interaction_pb2_grpc.InteractionStub, "CommentScores"),
            (r"^/likes/counts/batch$", interaction_pb2_grpc.InteractionStub, "LikeCounts"),
            (r"^/collects/counts/batch$", interaction_pb2_grpc.InteractionStub, "CollectCounts"),
            (r"^/focus/counts/batch$", interaction_pb2_grpc.InteractionStub, "FollowCounts"),
            (r"^/likes/user/[^/]+$", interaction_pb2_grpc.InteractionStub, "UserLikes"),
            (r"^/collects/user/[^/]+$", interaction_pb2_grpc.InteractionStub, "UserCollects"),
            (r"^/focus/count/follower/[^/]+$", interaction_pb2_grpc.InteractionStub, "UserFollowerCount"),
            (r"^/comments/internal/create$", interaction_pb2_grpc.InteractionStub, "CommentsCreate"),
            (r"^/articles/statistics/[^/]+$", statistics_pb2_grpc.StatisticsStub, "Article"),
            (r"^/(likes|collects)/statistics/[^/]+$", statistics_pb2_grpc.StatisticsStub, "Interaction"),
            (r"^/focus/statistics/[^/]+$", statistics_pb2_grpc.StatisticsStub, "Follow"),
            (r"^/(articles|likes|collects|focus)/[^/]+$", statistics_pb2_grpc.StatisticsStub, "UserPortrait"),
        )
    elif service_name == "nestjs":
        routes = (
            (r"^/article-logs/search-history/[^/]+$", log_pb2_grpc.LogStub, "SearchHistory"),
            (r"^/article-logs/view-distribution/[^/]+$", log_pb2_grpc.LogStub, "ViewDistribution"),
            (r"^/article-logs/search-keywords$", log_pb2_grpc.LogStub, "SearchKeywords"),
            (r"^/api-logs/average-speed$", log_pb2_grpc.LogStub, "ApiAverageSpeed"),
            (r"^/api-logs/called-count$", log_pb2_grpc.LogStub, "ApiCalledCount"),
        )
    else:
        return None

    for pattern, stub_type, method_name in routes:
        if re.match(pattern, path):
            return stub_type, method_name
    return None


def _metadata(headers: Dict[str, str]) -> Tuple[Tuple[str, str], ...]:
    values = []
    for key, value in headers.items():
        if value:
            values.append((key.lower(), value))
    return tuple(values)


def _request_payload(
    method: str,
    path: str,
    params: Optional[Dict[str, Any]],
    data: Optional[Dict[str, Any]],
    body: Optional[Dict[str, Any]],
) -> result_pb2.JsonRequest:
    payload = json.dumps(
        {"method": method, "path": path, "query": params or {}, "data": data, "body": body},
        ensure_ascii=False,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return result_pb2.JsonRequest(payload=payload)


async def call_grpc_if_supported(
    service_name: str,
    path: str,
    method: str,
    headers: Dict[str, str],
    params: Optional[Dict[str, Any]],
    data: Optional[Dict[str, Any]],
    body: Optional[Dict[str, Any]],
    timeout: int,
) -> Optional[Dict[str, Any]]:
    route = _match_rpc(service_name, path)
    if route is None:
        return None

    instance = get_service_instance(service_name)
    grpc_port = instance.get("metadata", {}).get("grpc_port") or instance.get("grpc_port")
    if not grpc_port:
        return None

    channel = grpc.aio.insecure_channel(f"{instance['ip']}:{grpc_port}")
    try:
        stub_type, method_name = route
        stub = stub_type(channel)
        response = await getattr(stub, method_name)(
            _request_payload(method, path, params, data, body),
            timeout=timeout / 1000,
            metadata=_metadata(headers),
        )
        result_data: Any = None
        if response.data:
            result_data = json.loads(response.data.decode("utf-8"))
        result: Dict[str, Any] = {
            "code": response.code,
            "msg": response.message,
            "data": result_data,
        }
        if response.code != HttpCode.OK:
            raise BusinessException(
                Messages.REMOTE_SERVICE_CALL_FAILED(service_name, response.message),
                HttpCode.BAD_GATEWAY,
                Messages.ERROR_SERVICE_CALL_FAILED,
            )
        return result
    except grpc.aio.AioRpcError as error:
        if error.code() not in (grpc.StatusCode.UNAVAILABLE, grpc.StatusCode.DEADLINE_EXCEEDED):
            raise
        Logger.warning(Messages.GRPC_CALL_FALLBACK(service_name, path, error))
        return None
    finally:
        await channel.close()
