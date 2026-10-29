class TelemetryConstants:
    """OpenTelemetry 配置与日志关联常量"""

    # ===== 采样器 =====

    SAMPLER_ALWAYS_ON: str = "always_on"
    """全量采样"""
    SAMPLER_ALWAYS_OFF: str = "always_off"
    """不采样"""
    SAMPLER_TRACE_ID_RATIO: str = "traceidratio"
    """按 trace id 比例采样"""
    SAMPLER_PARENT_ALWAYS_ON: str = "parentbased_always_on"
    """跟随父级上下文，父级存在时按父级决策，否则全量采样"""
    SAMPLER_PARENT_ALWAYS_OFF: str = "parentbased_always_off"
    """跟随父级上下文，父级存在时按父级决策，否则不采样"""
    SAMPLER_PARENT_TRACE_ID_RATIO: str = "parentbased_traceidratio"
    """跟随父级上下文，父级缺失时按 trace id 比例采样"""
    RESOURCE_SERVICE_NAME: str = "service.name"
    """资源属性中服务名的键"""

    # ===== 链路标识 =====

    TRACE_ID_HEX_WIDTH: int = 32
    """trace id 的十六进制字符长度"""
    EMPTY_TRACE_ID: str = "-"
    """无链路时使用的占位 trace id"""
    TRACE_ID_FIELD: str = "trace_id"
    """日志中链路标识的字段名"""
