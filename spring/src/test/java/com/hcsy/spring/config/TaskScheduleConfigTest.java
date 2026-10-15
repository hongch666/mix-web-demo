package com.hcsy.spring.config;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.runner.ApplicationContextRunner;

class TaskScheduleConfigTest {

    private final ApplicationContextRunner runner = new ApplicationContextRunner()
        .withUserConfiguration(TaskScheduleConfig.class);

    // 验证该场景的预期行为
    @Test
    @DisplayName("未声明 task.enabled 时默认启用调度配置")
    void enablesSchedulingWhenPropertyMissing() {
        runner.run(context -> assertThat(context).hasSingleBean(TaskScheduleConfig.class));
    }

    // 验证该场景的预期行为
    @Test
    @DisplayName("task.enabled=false 时不注册调度配置")
    void skipsSchedulingWhenDisabled() {
        runner.withPropertyValues("task.enabled=false")
            .run(context -> assertThat(context).doesNotHaveBean(TaskScheduleConfig.class));
    }
}
