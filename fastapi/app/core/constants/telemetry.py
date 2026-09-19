class TelemetryConstants:
    """OpenTelemetry 配置与日志关联常量"""

    SAMPLER_ALWAYS_ON: str = "always_on"
    SAMPLER_ALWAYS_OFF: str = "always_off"
    SAMPLER_TRACE_ID_RATIO: str = "traceidratio"
    SAMPLER_PARENT_ALWAYS_ON: str = "parentbased_always_on"
    SAMPLER_PARENT_ALWAYS_OFF: str = "parentbased_always_off"
    SAMPLER_PARENT_TRACE_ID_RATIO: str = "parentbased_traceidratio"
    RESOURCE_SERVICE_NAME: str = "service.name"

    TRACE_ID_HEX_WIDTH: int = 32
    EMPTY_TRACE_ID: str = "-"
    TRACE_ID_FIELD: str = "trace_id"
