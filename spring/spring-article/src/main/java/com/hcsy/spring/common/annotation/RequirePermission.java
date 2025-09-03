package com.hcsy.spring.common.annotation;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
public @interface RequirePermission {
    /**
     * 需要的角色
     */
    String[] roles() default {};

    /**
     * 是否允许操作自己的数据
     */
    boolean allowSelf() default false;

    /**
     * 目标用户ID的参数名
     */
    String targetUserIdParam() default "id";
}