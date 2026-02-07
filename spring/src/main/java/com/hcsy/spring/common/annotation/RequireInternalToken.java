package com.hcsy.spring.common.annotation;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

/**
 * 需要服务内部令牌的注解
 * 用于标记需要验证内部服务令牌的接口方法
 * 只有带有有效的 X-Internal-Token 请求头的请求才能访问
 * 
 * @author hcsy
 */
@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
public @interface RequireInternalToken {
    /**
     * 服务名称，用于令牌验证
     * 
     * @return 调用者的服务名称
     */
    String value() default "";
}
