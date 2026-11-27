package com.hcsy.spring.web.logging.annotation;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

/**
 * API 日志注解
 * 用于自动记录 API 请求日志
 *
 * @author hcsy
 */
@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
public @interface ApiLog {

    /**
     * 日志消息
     *
     * @return 日志消息
     */
    String value();

    /**
     * 是否包含参数信息
     *
     * @return true-包含参数，false-不包含参数
     */
    boolean includeParams() default true;

    /**
     * 日志级别
     *
     * @return 日志级别
     */
    LogLevel level() default LogLevel.INFO;

    /**
     * 排除的字段名称（用于排除敏感信息）
     *
     * @return 排除的字段名称数组
     */
    String[] excludeFields() default {};

    /**
     * 是否跳过接口日志的 MQ 投递，只保留本地日志，用于测试接口与内部令牌接口
     *
     * @return true-不投递 MQ，false-投递 MQ
     */
    boolean skipMq() default false;

    /**
     * 日志级别枚举
     */
    enum LogLevel {
        INFO, WARN, ERROR
    }
}
