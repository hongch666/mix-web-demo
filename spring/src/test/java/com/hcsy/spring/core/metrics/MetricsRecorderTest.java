package com.hcsy.spring.core.metrics;

import static org.junit.jupiter.api.Assertions.assertEquals;

import java.util.concurrent.TimeUnit;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import com.hcsy.spring.common.constants.MetricNames;

import io.micrometer.core.instrument.simple.SimpleMeterRegistry;

class MetricsRecorderTest {

    private final SimpleMeterRegistry meterRegistry = new SimpleMeterRegistry();

    private final MetricsRecorder metricsRecorder = new MetricsRecorder(meterRegistry);

    // 验证该场景的预期行为
    @Test
    @DisplayName("记录下游调用次数与耗时并绑定标签")
    void recordsClientCallCounterAndTimer() {
        metricsRecorder.recordClientCall("spring", "GET", "success", 1500L);

        assertEquals(1.0, meterRegistry.get(MetricNames.CLIENT_REQUESTS)
            .tags("target_service", "spring", "method", "GET", "outcome", "success").counter().count());
        assertEquals(1L, meterRegistry.get(MetricNames.CLIENT_DURATION)
            .tags("target_service", "spring", "method", "GET").timer().count());
        assertEquals(1500.0, meterRegistry.get(MetricNames.CLIENT_DURATION)
            .tags("target_service", "spring", "method", "GET").timer().totalTime(TimeUnit.NANOSECONDS));
    }

    // 验证该场景的预期行为
    @Test
    @DisplayName("自定义计数指标按标签分别累加")
    void incrementsNamedCounterWithTags() {
        metricsRecorder.increment(MetricNames.USER_LOGIN, "result", "success");
        metricsRecorder.increment(MetricNames.USER_LOGIN, "result", "success");
        metricsRecorder.increment(MetricNames.USER_LOGIN, "result", "failure");

        assertEquals(2.0, meterRegistry.get(MetricNames.USER_LOGIN).tags("result", "success").counter().count());
        assertEquals(1.0, meterRegistry.get(MetricNames.USER_LOGIN).tags("result", "failure").counter().count());
    }

    // 验证该场景的预期行为
    @Test
    @DisplayName("记录定时任务次数与耗时并绑定标签")
    void recordsTaskCounterAndTimer() {
        metricsRecorder.recordTask("token-cleanup", "failure", 2000L);

        assertEquals(1.0, meterRegistry.get(MetricNames.TASK_RUNS)
            .tags("task", "token-cleanup", "result", "failure").counter().count());
        assertEquals(1L,
            meterRegistry.get(MetricNames.TASK_DURATION).tags("task", "token-cleanup").timer().count());
        assertEquals(2000.0, meterRegistry.get(MetricNames.TASK_DURATION).tags("task", "token-cleanup").timer()
            .totalTime(TimeUnit.NANOSECONDS));
    }
}
