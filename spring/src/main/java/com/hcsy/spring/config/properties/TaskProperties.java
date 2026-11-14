package com.hcsy.spring.config.properties;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.boot.context.properties.bind.DefaultValue;

/**
 * 定时任务配置属性（构造器绑定，不可变）
 *
 * @param enabled 是否启用本地 @Scheduled 调度能力，false 时任务改由外部调度器触发
 */
@ConfigurationProperties(prefix = "task")
public record TaskProperties(@DefaultValue("true") boolean enabled) {
}
