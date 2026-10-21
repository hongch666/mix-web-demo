package com.hcsy.spring.observability;

import java.util.concurrent.TimeUnit;

import org.springframework.stereotype.Component;

import com.hcsy.spring.common.constants.MetricNames;

import io.micrometer.core.instrument.MeterRegistry;
import lombok.RequiredArgsConstructor;

/**
 * 封装基于 Micrometer 的指标记录能力，覆盖微服务调用与后台任务的次数和耗时
 */
@Component
@RequiredArgsConstructor
public class MetricsRecorder {

    private final MeterRegistry meterRegistry;

    /**
     * 记录微服务间调用的请求次数与耗时指标
     */
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

    /**
     * 按标签递增指定名称的计数器指标
     */
    public void increment(String name, String... tags) {
        meterRegistry.counter(name, tags).increment();
    }

    /**
     * 记录后台任务的执行次数与耗时指标
     */
    public void recordTask(String task, String result, long durationNanos) {
        meterRegistry.counter(MetricNames.TASK_RUNS, "task", task, "result", result).increment();
        meterRegistry.timer(MetricNames.TASK_DURATION, "task", task)
            .record(durationNanos, TimeUnit.NANOSECONDS);
    }
}
