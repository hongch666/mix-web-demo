package com.hcsy.spring.web.security.annotation;

import java.lang.annotation.Documented;
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
@Documented
public @interface RequireInternalToken {
}
