from collections.abc import Generator
from typing import Any

import pytest
from fastapi import FastAPI
from opentelemetry.sdk.trace.sampling import ALWAYS_ON, TraceIdRatioBased
from prometheus_client import REGISTRY

from app.core.constants import Messages, TelemetryConstants
from app.core.telemetry import instrumentation


class FakeInstrumentor:
    """埋点替身, 同时充当工厂与调用记录器"""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def __call__(self) -> "FakeInstrumentor":
        return self

    def instrument(self, **kwargs: Any) -> None:
        self.calls.append(kwargs)

    def instrument_app(self, app: Any, **kwargs: Any) -> None:
        self.calls.append({"app": app, **kwargs})


class FakeSpanExporter:
    def __init__(self, endpoint: str) -> None:
        self.endpoint = endpoint


class FakeSpanProcessor:
    def __init__(self, exporter: Any) -> None:
        self.exporter = exporter


class FakeTracerProvider:
    def __init__(self, resource: Any = None, sampler: Any = None) -> None:
        self.resource = resource
        self.sampler = sampler
        self.span_processors: list[Any] = []
        self.shutdown_called = False

    def add_span_processor(self, processor: Any) -> None:
        self.span_processors.append(processor)

    def shutdown(self) -> None:
        self.shutdown_called = True


class FakeMeterProvider:
    def __init__(self, resource: Any = None, metric_readers: Any = None) -> None:
        self.resource = resource
        self.metric_readers = metric_readers
        self.shutdown_called = False

    def shutdown(self) -> None:
        self.shutdown_called = True


class FakeMetricsServer:
    def __init__(self) -> None:
        self.shutdown_called = False

    def shutdown(self) -> None:
        self.shutdown_called = True


class FakeStartHttpServer:
    """记录 start_http_server 入参并返回固定指标服务替身"""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []
        self.server = FakeMetricsServer()

    def __call__(
        self, port: int, registry: Any = None
    ) -> tuple[FakeMetricsServer, None]:
        self.calls.append({"port": port, "registry": registry})
        return self.server, None


@pytest.fixture(autouse=True)
def reset_telemetry_globals() -> Generator[None, None, None]:
    """模块级单例在每个用例前后都要还原, 避免用例互相污染"""
    instrumentation._provider = None
    instrumentation._meter_provider = None
    instrumentation._metrics_server = None
    yield
    instrumentation._provider = None
    instrumentation._meter_provider = None
    instrumentation._metrics_server = None


def _telemetry_config(**overrides: Any) -> dict[str, Any]:
    config: dict[str, Any] = {
        "enabled": True,
        "service_name": "fastapi",
        "traces_endpoint": "http://collector:4318/v1/traces",
        "sampler": TelemetryConstants.SAMPLER_ALWAYS_ON,
        "sampler_arg": "",
        "metrics_port": 9464,
    }
    config.update(overrides)
    return config


# 采样比例接受 0 与 1 的边界值并按原样构造采样器
@pytest.mark.parametrize("ratio_value", ["0", "0.25", "1"])
def test_create_ratio_sampler_accepts_valid_ratios(ratio_value: str) -> None:
    sampler = instrumentation._create_ratio_sampler(ratio_value)

    assert isinstance(sampler, TraceIdRatioBased)
    assert sampler.get_description() == f"TraceIdRatioBased{{{float(ratio_value)}}}"


# 非法字符串、越界比例与非数字统一转成带中文消息的 ValueError
@pytest.mark.parametrize("ratio_value", ["abc", "-0.1", "1.5", None])
def test_create_ratio_sampler_rejects_invalid_ratios(ratio_value: Any) -> None:
    with pytest.raises(ValueError) as error:
        instrumentation._create_ratio_sampler(ratio_value)

    assert str(error.value) == Messages.OTEL_INVALID_SAMPLER_RATIO(ratio_value)


# 六种采样器名各自映射到对应的采样实现
@pytest.mark.parametrize(
    ("sampler_name", "sampler_arg", "expected_description"),
    [
        (TelemetryConstants.SAMPLER_ALWAYS_ON, "", "AlwaysOnSampler"),
        (TelemetryConstants.SAMPLER_ALWAYS_OFF, "", "AlwaysOffSampler"),
        (TelemetryConstants.SAMPLER_TRACE_ID_RATIO, "0.5", "TraceIdRatioBased{0.5}"),
        (
            TelemetryConstants.SAMPLER_PARENT_ALWAYS_ON,
            "",
            "ParentBased{root:AlwaysOnSampler,",
        ),
        (
            TelemetryConstants.SAMPLER_PARENT_ALWAYS_OFF,
            "",
            "ParentBased{root:AlwaysOffSampler,",
        ),
        (
            TelemetryConstants.SAMPLER_PARENT_TRACE_ID_RATIO,
            "0.25",
            "ParentBased{root:TraceIdRatioBased{0.25},",
        ),
    ],
)
def test_create_sampler_dispatches_supported_names(
    sampler_name: str, sampler_arg: str, expected_description: str
) -> None:
    sampler = instrumentation._create_sampler(
        {"sampler": sampler_name, "sampler_arg": sampler_arg}
    )

    assert sampler.get_description().startswith(expected_description)


# 未登记的采样器名直接拒绝启动而不是回退到默认采样
def test_create_sampler_rejects_unsupported_name() -> None:
    with pytest.raises(ValueError) as error:
        instrumentation._create_sampler({"sampler": "unknown", "sampler_arg": ""})

    assert str(error.value) == Messages.OTEL_UNSUPPORTED_SAMPLER("unknown")


# 关闭遥测时不创建任何 provider 与指标端点
def test_setup_telemetry_returns_none_when_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        instrumentation, "load_config", lambda key: _telemetry_config(enabled=False)
    )

    assert instrumentation.setup_telemetry() is None
    assert instrumentation._provider is None
    assert instrumentation._meter_provider is None
    assert instrumentation._metrics_server is None


# 已初始化时直接复用 provider, 不再读取配置
def test_setup_telemetry_reuses_initialized_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cached_provider = FakeTracerProvider()
    load_config_calls: list[str] = []
    monkeypatch.setattr(instrumentation, "_provider", cached_provider)
    monkeypatch.setattr(
        instrumentation,
        "load_config",
        lambda key: load_config_calls.append(key) or _telemetry_config(),
    )

    assert instrumentation.setup_telemetry() is cached_provider
    assert load_config_calls == []


# 启用遥测时按配置装配 SDK 并启动指标端点
def test_setup_telemetry_configures_sdk_and_starts_metrics_server(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(instrumentation, "load_config", lambda key: _telemetry_config())
    monkeypatch.setattr(instrumentation, "TracerProvider", FakeTracerProvider)
    monkeypatch.setattr(instrumentation, "BatchSpanProcessor", FakeSpanProcessor)
    monkeypatch.setattr(instrumentation, "OTLPSpanExporter", FakeSpanExporter)
    monkeypatch.setattr(instrumentation, "MeterProvider", FakeMeterProvider)

    tracer_provider_calls: list[Any] = []
    meter_provider_calls: list[Any] = []
    monkeypatch.setattr(
        instrumentation.trace, "set_tracer_provider", tracer_provider_calls.append
    )
    monkeypatch.setattr(
        instrumentation.metrics, "set_meter_provider", meter_provider_calls.append
    )

    http_server = FakeStartHttpServer()
    monkeypatch.setattr(instrumentation, "start_http_server", http_server)

    httpx_instrumentor = FakeInstrumentor()
    sqlalchemy_instrumentor = FakeInstrumentor()
    redis_instrumentor = FakeInstrumentor()
    monkeypatch.setattr(instrumentation, "HTTPXClientInstrumentor", httpx_instrumentor)
    monkeypatch.setattr(
        instrumentation, "SQLAlchemyInstrumentor", sqlalchemy_instrumentor
    )
    monkeypatch.setattr(instrumentation, "RedisInstrumentor", redis_instrumentor)

    provider = instrumentation.setup_telemetry()

    assert isinstance(provider, FakeTracerProvider)
    assert (
        provider.resource.attributes[TelemetryConstants.RESOURCE_SERVICE_NAME]
        == "fastapi"
    )
    assert provider.sampler is ALWAYS_ON
    assert isinstance(provider.span_processors[0], FakeSpanProcessor)
    assert (
        provider.span_processors[0].exporter.endpoint
        == "http://collector:4318/v1/traces"
    )
    assert tracer_provider_calls == [provider]

    assert isinstance(instrumentation._meter_provider, FakeMeterProvider)
    assert meter_provider_calls == [instrumentation._meter_provider]
    assert http_server.calls == [{"port": 9464, "registry": REGISTRY}]
    assert instrumentation._metrics_server is http_server.server

    assert httpx_instrumentor.calls == [{"tracer_provider": provider}]
    assert sqlalchemy_instrumentor.calls == [{"tracer_provider": provider}]
    assert redis_instrumentor.calls == [{"tracer_provider": provider}]


# 未初始化 provider 时不为应用安装追踪中间件
def test_instrument_fastapi_skips_when_provider_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    instrumentor = FakeInstrumentor()
    monkeypatch.setattr(instrumentation, "FastAPIInstrumentor", instrumentor)

    instrumentation.instrument_fastapi(FastAPI())

    assert instrumentor.calls == []


# 已初始化时把应用与两个 provider 交给 FastAPIInstrumentor
def test_instrument_fastapi_installs_tracing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tracer_provider = FakeTracerProvider()
    meter_provider = FakeMeterProvider()
    instrumentor = FakeInstrumentor()
    monkeypatch.setattr(instrumentation, "_provider", tracer_provider)
    monkeypatch.setattr(instrumentation, "_meter_provider", meter_provider)
    monkeypatch.setattr(instrumentation, "FastAPIInstrumentor", instrumentor)
    app = FastAPI()

    instrumentation.instrument_fastapi(app)

    assert instrumentor.calls == [
        {
            "app": app,
            "tracer_provider": tracer_provider,
            "meter_provider": meter_provider,
        }
    ]


# 关闭时依次释放追踪、指标与指标端点资源
def test_shutdown_telemetry_releases_all_resources(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tracer_provider = FakeTracerProvider()
    meter_provider = FakeMeterProvider()
    metrics_server = FakeMetricsServer()
    monkeypatch.setattr(instrumentation, "_provider", tracer_provider)
    monkeypatch.setattr(instrumentation, "_meter_provider", meter_provider)
    monkeypatch.setattr(instrumentation, "_metrics_server", metrics_server)

    instrumentation.shutdown_telemetry()

    assert tracer_provider.shutdown_called is True
    assert meter_provider.shutdown_called is True
    assert metrics_server.shutdown_called is True


# 从未初始化过遥测时关闭动作直接返回, 不创建也不释放任何资源
def test_shutdown_telemetry_without_initialized_resources() -> None:
    instrumentation.shutdown_telemetry()

    assert instrumentation._provider is None
    assert instrumentation._meter_provider is None
    assert instrumentation._metrics_server is None
