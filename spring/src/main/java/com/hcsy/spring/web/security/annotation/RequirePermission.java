package com.hcsy.spring.web.security.annotation;

import java.lang.annotation.Documented;
import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

import com.hcsy.spring.common.constants.BusinessType;
import com.hcsy.spring.common.constants.ParamSource;

/**
 * 声明式权限校验注解
 * 切面先校验角色，角色不匹配时按 allowSelf 判断当前用户是否为目标资源所有者
 */
@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
@Documented
public @interface RequirePermission {

    /**
     * 允许访问的角色，为空表示只校验所有权
     */
    String[] roles() default {};

    /**
     * 是否允许操作自己的数据
     */
    boolean allowSelf() default false;

    /**
     * 业务资源类型，决定归属校验查询哪张资源表
     */
    BusinessType businessType() default BusinessType.USER;

    /**
     * 目标资源标识的参数来源
     */
    ParamSource paramSource() default ParamSource.PATH_SINGLE;

    /**
     * 目标资源标识的参数名称，可以是路径参数名、查询参数名或请求体属性名
     */
    String paramName() default "id";
}
