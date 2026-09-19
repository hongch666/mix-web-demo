package com.hcsy.spring.common.constants;

/**
 * OpenTelemetry 日志关联常量
 */
public final class TelemetryConstants {

    private TelemetryConstants() {
    }

    public static final String EMPTY_TRACE_ID = "-";
    public static final String LOG_ENTRY_FORMAT = "%s - %s - trace_id=%s - %s%n";
}
