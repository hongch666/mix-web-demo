package com.hcsy.spring.web.swagger.annotation;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

/**
 * {@link ApiErrorCode} 的容器注解，支持在同一接口上重复声明多个业务错误码
 */
@Target({ ElementType.METHOD, ElementType.TYPE })
@Retention(RetentionPolicy.RUNTIME)
public @interface ApiErrorCodes {

    /** 业务错误码声明列表 */
    ApiErrorCode[] value();
}
