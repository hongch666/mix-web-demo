package com.hcsy.spring.config.properties;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.boot.context.properties.bind.DefaultValue;

/**
 * 日志配置属性（构造器绑定，不可变）
 *
 * @param includeTimestamp 是否在文件日志行写入时间戳，容器部署置 false，由 Loki 采集时间承担，避免同一行出现两个日期
 */
@ConfigurationProperties(prefix = "logging")
public record LoggingProperties(@DefaultValue("true") boolean includeTimestamp) {
}
