package com.hcsy.spring.config.properties;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.boot.context.properties.bind.DefaultValue;

/**
 * 日志文件输出配置属性（构造器绑定，不可变）
 *
 * @param path 日志文件输出目录
 */
@ConfigurationProperties(prefix = "logging.file")
public record LoggingFileProperties(@DefaultValue("../logs/spring") String path) {
}
