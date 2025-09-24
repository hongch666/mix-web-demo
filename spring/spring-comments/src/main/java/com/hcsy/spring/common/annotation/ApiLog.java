package com.hcsy.spring.common.annotation;

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
     * 日志级别枚举
     */
    enum LogLevel {
        INFO, WARN, ERROR
    }
}