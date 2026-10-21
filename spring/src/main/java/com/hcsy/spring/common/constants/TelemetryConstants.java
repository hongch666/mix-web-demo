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

    public static final String EMPTY_TRACE_ID = "-";
    public static final String LOG_ENTRY_FORMAT = "%s - %s - trace_id=%s - %s%n";
}
