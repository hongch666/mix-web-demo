package com.hcsy.spring.config;

import org.springframework.boot.context.properties.bind.Bindable;
import org.springframework.boot.context.properties.bind.Binder;
import org.springframework.context.annotation.Condition;
import org.springframework.context.annotation.ConditionContext;
import org.springframework.context.annotation.Conditional;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.type.AnnotatedTypeMetadata;
import org.springframework.scheduling.annotation.EnableScheduling;

import com.hcsy.spring.config.properties.TaskProperties;

/**
 * 定时任务调度注册配置
 *
 * task.enabled 为 false 时不启用调度能力，本地 @Scheduled 任务不会注册
 * 任务改由外部调度器（DolphinScheduler）触发 /task/* 手动入口，控制器与任务 Bean 仍然可用
 */
@Configuration
@EnableScheduling
@Conditional(TaskScheduleConfig.EnabledCondition.class)
public class TaskScheduleConfig {

    /**
     * 定时任务开关条件，仅本配置使用
     *
     * 条件装配阶段还没有 TaskProperties Bean，改用 Binder 直接按 task 前缀绑定 TaskProperties 判定，未配置时取 @DefaultValue 的 true
     */
    public static class EnabledCondition implements Condition {

        /**
         * 按 task.enabled 判定是否启用本地调度能力
         *
         * @param context  条件上下文，从中取 Environment 做属性绑定
         * @param metadata 被条件标注的类型元数据
         * @return task.enabled 为 true 时返回 true，未配置时取 TaskProperties 默认值
         */
        @Override
        public boolean matches(ConditionContext context, AnnotatedTypeMetadata metadata) {
            Binder binder = Binder.get(context.getEnvironment());
            return binder.bindOrCreate("task", Bindable.of(TaskProperties.class)).enabled();
        }
    }
}
