import pytest

from app.core.client.grpc_client import _match_rpc


@pytest.mark.parametrize(
    ("service", "path", "method"),
    [
        ("spring", "/articles/batch", "Batch"),
        ("spring", "/articles/123", "Get"),
        ("spring", "/category/internal/all", "All"),
        ("spring", "/users/batch", "Batch"),
        ("spring", "/likes/counts/batch", "LikeCounts"),
        ("spring", "/articles/statistics/top10", "Article"),
        ("nestjs", "/article-logs/search-history/101", "SearchHistory"),
        ("nestjs", "/api-logs/called-count", "ApiCalledCount"),
    ],
)
def test_grpc_route_mapping(service: str, path: str, method: str) -> None:
    route = _match_rpc(service, path)
    assert route is not None
    assert route[1] == method


def test_long_lived_http_endpoint_is_not_grpc() -> None:
    assert _match_rpc("spring", "/warehouse/sync/article") is None
    assert _match_rpc("spring", "/articles/statistics/excel-export") is None
    assert _match_rpc("nestjs", "/upload") is None
