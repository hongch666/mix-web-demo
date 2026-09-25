from typing import Any, Optional

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry import metrics
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import (
    ALWAYS_OFF,
    ALWAYS_ON,
    ParentBased,
    Sampler,
    TraceIdRatioBased,
)
from prometheus_client import REGISTRY, start_http_server

from app.core.config import load_config
from app.core.constants import Messages, TelemetryConstants

_provider: Optional[TracerProvider] = None
_meter_provider: Optional[MeterProvider] = None
_metrics_server: Any = None


def _create_ratio_sampler(ratio_value: Any) -> TraceIdRatioBased:
    try:
        ratio: float = float(ratio_value)
    except (TypeError, ValueError) as error:
        raise ValueError(Messages.OTEL_INVALID_SAMPLER_RATIO(ratio_value)) from error
    if ratio < 0 or ratio > 1:
        raise ValueError(Messages.OTEL_INVALID_SAMPLER_RATIO(ratio_value))
    return TraceIdRatioBased(ratio)


def _create_sampler(config: dict[str, Any]) -> Sampler:
    sampler_name: str = str(config["sampler"])
    if sampler_name == TelemetryConstants.SAMPLER_ALWAYS_ON:
        return ALWAYS_ON
    if sampler_name == TelemetryConstants.SAMPLER_ALWAYS_OFF:
        return ALWAYS_OFF
    if sampler_name == TelemetryConstants.SAMPLER_TRACE_ID_RATIO:
        return _create_ratio_sampler(config["sampler_arg"])
    if sampler_name == TelemetryConstants.SAMPLER_PARENT_ALWAYS_ON:
        return ParentBased(ALWAYS_ON)
    if sampler_name == TelemetryConstants.SAMPLER_PARENT_ALWAYS_OFF:
        return ParentBased(ALWAYS_OFF)
    if sampler_name == TelemetryConstants.SAMPLER_PARENT_TRACE_ID_RATIO:
        return ParentBased(_create_ratio_sampler(config["sampler_arg"]))
    raise ValueError(Messages.OTEL_UNSUPPORTED_SAMPLER(sampler_name))


def setup_telemetry() -> Optional[TracerProvider]:
    """初始化进程级追踪，并在数据库引擎创建前安装自动埋点"""
    global _provider, _meter_provider, _metrics_server
    if _provider is not None:
        return _provider

    telemetry_config: dict[str, Any] = load_config("telemetry")
    if not telemetry_config["enabled"]:
        return None

    resource = Resource.create(
        {TelemetryConstants.RESOURCE_SERVICE_NAME: telemetry_config["service_name"]}
    )
    provider = TracerProvider(
        resource=resource,
        sampler=_create_sampler(telemetry_config),
    )
    provider.add_span_processor(
        BatchSpanProcessor(
            OTLPSpanExporter(endpoint=telemetry_config["traces_endpoint"])
        )
    )
    trace.set_tracer_provider(provider)

    metric_reader = PrometheusMetricReader(registry=REGISTRY)
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)
    _meter_provider = meter_provider
    _metrics_server, _ = start_http_server(
        port=int(telemetry_config["metrics_port"]), registry=REGISTRY
    )

    HTTPXClientInstrumentor().instrument(tracer_provider=provider)
    SQLAlchemyInstrumentor().instrument(tracer_provider=provider)
    RedisInstrumentor().instrument(tracer_provider=provider)
    _provider = provider
    return provider


def instrument_fastapi(app: FastAPI) -> None:
    """为应用安装 ASGI 追踪中间件"""
    if _provider is not None:
        FastAPIInstrumentor.instrument_app(
            app, tracer_provider=_provider, meter_provider=_meter_provider
        )


def shutdown_telemetry() -> None:
    """刷新并关闭追踪导出器"""
    if _provider is not None:
        _provider.shutdown()
    if _meter_provider is not None:
        _meter_provider.shutdown()
    if _metrics_server is not None:
        _metrics_server.shutdown()
