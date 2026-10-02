package com.hcsy.spring.core.metrics;

import java.util.concurrent.TimeUnit;

import org.springframework.stereotype.Component;

import com.hcsy.spring.common.constants.MetricNames;

import io.micrometer.core.instrument.MeterRegistry;
import lombok.RequiredArgsConstructor;

@Component
@RequiredArgsConstructor
public class MetricsRecorder {

    private final MeterRegistry meterRegistry;

    public void recordClientCall(String targetService, String method, String outcome, long durationNanos) {
        meterRegistry.counter(
            MetricNames.CLIENT_REQUESTS,
            "target_service", targetService,
            "method", method,
            "outcome", outcome).increment();
        meterRegistry.timer(
            MetricNames.CLIENT_DURATION,
            "target_service", targetService,
            "method", method).record(durationNanos, TimeUnit.NANOSECONDS);
    }

    public void increment(String name, String... tags) {
        meterRegistry.counter(name, tags).increment();
    }

    public void recordTask(String task, String result, long durationNanos) {
        meterRegistry.counter(MetricNames.TASK_RUNS, "task", task, "result", result).increment();
        meterRegistry.timer(MetricNames.TASK_DURATION, "task", task)
            .record(durationNanos, TimeUnit.NANOSECONDS);
    }
}
