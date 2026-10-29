package com.hcsy.spring.common.constants;

/**
 * OpenTelemetry 日志关联常量
 */
public final class TelemetryConstants {

    /**
     * 聚合 OpenTelemetry 日志关联的 traceId 占位符与日志行格式常量
     */
    private TelemetryConstants() {
    }

    // ===== 链路标识 =====

    /** 无活动链路时使用的占位 traceId */
    public static final String EMPTY_TRACE_ID = "-";
    /** 带时间戳的日志行格式 */
    public static final String LOG_ENTRY_FORMAT = "%s - %s - trace_id=%s - %s%n";

    /**
     * 不写时间戳的日志行格式，用于容器部署（时间戳由 Loki 采集侧提供，避免同一行出现两个日期）
     */
    public static final String LOG_ENTRY_FORMAT_NO_TIMESTAMP = "%s - trace_id=%s - %s%n";
}
