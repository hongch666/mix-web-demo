from unittest.mock import AsyncMock, Mock

import pytest

from app.internal.services.apiLog import apiLogService as service_module
from app.internal.services.apiLog.apiLogService import ApiLogService


@pytest.fixture(autouse=True)
def _silence_logger(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(service_module, "Logger", Mock())


def _make_service() -> tuple[ApiLogService, AsyncMock, AsyncMock]:
    nestjs_client = AsyncMock()
    api_log_mapper = AsyncMock()
    return ApiLogService(nestjs_client, api_log_mapper), nestjs_client, api_log_mapper


# ClickHouse 返回数据时直接采用且不调用 NestJS
@pytest.mark.anyio
async def test_average_speed_prefers_ads_result() -> None:
    service, nestjs, mapper = _make_service()
    ads_rows = [{"api_path": "/a", "avg_response_time": 1.5}]
    mapper.get_api_average_speed_clickhouse_mapper_async.return_value = ads_rows

    result = await service.get_api_average_response_time_service()

    assert result is ads_rows
    mapper.get_api_average_speed_clickhouse_mapper_async.assert_awaited_once()
    nestjs.get_api_average_speed.assert_not_awaited()


# ClickHouse 返回空列表时降级调用 NestJS 平均耗时
@pytest.mark.anyio
async def test_average_speed_falls_back_when_ads_empty() -> None:
    service, nestjs, mapper = _make_service()
    mapper.get_api_average_speed_clickhouse_mapper_async.return_value = []
    nestjs.get_api_average_speed.return_value = [{"from": "remote"}]

    result = await service.get_api_average_response_time_service()

    assert result == [{"from": "remote"}]
    mapper.get_api_average_speed_clickhouse_mapper_async.assert_awaited_once()
    nestjs.get_api_average_speed.assert_awaited_once_with()


# ClickHouse 抛异常时降级调用 NestJS 平均耗时
@pytest.mark.anyio
async def test_average_speed_falls_back_when_ads_raises() -> None:
    service, nestjs, mapper = _make_service()
    mapper.get_api_average_speed_clickhouse_mapper_async.side_effect = RuntimeError(
        "clickhouse down"
    )
    nestjs.get_api_average_speed.return_value = [{"from": "remote"}]

    result = await service.get_api_average_response_time_service()

    assert result == [{"from": "remote"}]
    nestjs.get_api_average_speed.assert_awaited_once_with()


# ClickHouse 有数据时直接返回调用次数且不调 NestJS
@pytest.mark.anyio
async def test_called_count_prefers_ads_result() -> None:
    service, nestjs, mapper = _make_service()
    ads_rows = [{"api_path": "/b", "call_count": 12}]
    mapper.get_called_count_clickhouse_mapper_async.return_value = ads_rows

    assert await service.get_called_count_apis_service() is ads_rows
    nestjs.get_called_count.assert_not_awaited()


# ClickHouse 返回空时降级到 NestJS 调用次数
@pytest.mark.anyio
async def test_called_count_falls_back_when_ads_empty() -> None:
    service, nestjs, mapper = _make_service()
    mapper.get_called_count_clickhouse_mapper_async.return_value = []
    nestjs.get_called_count.return_value = [{"from": "remote"}]

    assert await service.get_called_count_apis_service() == [{"from": "remote"}]
    nestjs.get_called_count.assert_awaited_once_with()


# ClickHouse 抛异常时降级到 NestJS 调用次数
@pytest.mark.anyio
async def test_called_count_falls_back_when_ads_raises() -> None:
    service, nestjs, mapper = _make_service()
    mapper.get_called_count_clickhouse_mapper_async.side_effect = RuntimeError(
        "clickhouse down"
    )
    nestjs.get_called_count.return_value = [{"from": "remote"}]

    assert await service.get_called_count_apis_service() == [{"from": "remote"}]
    nestjs.get_called_count.assert_awaited_once_with()


# ClickHouse 与 NestJS 均失败时向上抛出远程错误
@pytest.mark.anyio
async def test_remote_failure_propagates_when_ads_unavailable() -> None:
    service, nestjs, mapper = _make_service()
    mapper.get_api_average_speed_clickhouse_mapper_async.side_effect = RuntimeError(
        "clickhouse down"
    )
    nestjs.get_api_average_speed.side_effect = RuntimeError("remote down")

    with pytest.raises(RuntimeError, match="remote down"):
        await service.get_api_average_response_time_service()
