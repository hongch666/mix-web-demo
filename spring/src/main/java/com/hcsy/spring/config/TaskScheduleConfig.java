package com.hcsy.spring.config;

import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.annotation.EnableScheduling;

/**
 * 定时任务调度注册配置
 *
 * task.enabled 为 false 时不启用调度能力，本地 @Scheduled 任务不会注册
 * 任务改由外部调度器（DolphinScheduler）触发 /task/* 手动入口，控制器与任务 Bean 仍然可用
 */
@Configuration
@EnableScheduling
@ConditionalOnProperty(prefix = "task", name = "enabled", havingValue = "true", matchIfMissing = true)
public class TaskScheduleConfig {
}
