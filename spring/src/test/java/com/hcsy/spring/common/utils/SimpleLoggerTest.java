package com.hcsy.spring.common.utils;

import static org.assertj.core.api.Assertions.assertThat;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.stream.Stream;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import com.hcsy.spring.config.properties.LoggingFileProperties;
import com.hcsy.spring.config.properties.LoggingProperties;

import io.opentelemetry.api.trace.Span;
import io.opentelemetry.api.trace.SpanContext;
import io.opentelemetry.api.trace.TraceFlags;
import io.opentelemetry.api.trace.TraceState;
import io.opentelemetry.context.Scope;

class SimpleLoggerTest {

    @TempDir
    Path logDirectory;

    // 验证该场景的预期行为

    @Test
    void shouldWriteCurrentTraceIdToFile() throws Exception {
        SimpleLogger logger = new SimpleLogger(
            new LoggingProperties(true),
            new LoggingFileProperties(logDirectory.toString()));
        logger.init();
        String traceId = "0123456789abcdef0123456789abcdef";
        SpanContext spanContext = SpanContext.create(
            traceId,
            "0123456789abcdef",
            TraceFlags.getSampled(),
            TraceState.getDefault());

        try (Scope ignored = Span.wrap(spanContext).makeCurrent()) {
            logger.info("链路日志");
        }

        try (Stream<Path> logFiles = Files.list(logDirectory)) {
            Path logFile = logFiles.findFirst().orElseThrow();
            assertThat(Files.readString(logFile)).contains("trace_id=" + traceId);
        }
    }

    @Test
    void shouldOmitTimestampWhenDisabled() throws Exception {
        SimpleLogger logger = new SimpleLogger(
            new LoggingProperties(false),
            new LoggingFileProperties(logDirectory.toString()));
        logger.init();

        logger.info("无时间戳日志");

        try (Stream<Path> logFiles = Files.list(logDirectory)) {
            Path logFile = logFiles.findFirst().orElseThrow();
            assertThat(Files.readString(logFile)).startsWith("INFO - trace_id=- - 无时间戳日志");
        }
    }
}
