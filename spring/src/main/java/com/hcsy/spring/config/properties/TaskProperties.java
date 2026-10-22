package com.hcsy.spring.config.properties;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.boot.context.properties.bind.DefaultValue;

/**
 * 定时任务配置属性（构造器绑定，不可变）
 *
 * @param enabled 定时任务开关，false 时不注册本地 @Scheduled 任务，改由外部调度器触发 /task/* 接口
 */
@ConfigurationProperties(prefix = "task")
public record TaskProperties(@DefaultValue("true") boolean enabled) {
}
