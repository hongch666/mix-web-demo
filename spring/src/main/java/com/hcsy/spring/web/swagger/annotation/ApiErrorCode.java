package com.hcsy.spring.web.swagger.annotation;

import java.lang.annotation.ElementType;
import java.lang.annotation.Repeatable;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

/**
 * 声明接口可能返回的业务错误码，供 OpenAPI 文档补充错误响应
 *
 * 不使用 springdoc 的 @ApiResponse：在 2.6 里方法级 @ApiResponse 会覆盖自动生成的 200 成功响应，
 * 本注解不参与 springdoc 的响应解析，由 SwaggerConfig 的 OperationCustomizer 读取后注入统一错误体
 */
@Target({ ElementType.METHOD, ElementType.TYPE })
@Retention(RetentionPolicy.RUNTIME)
@Repeatable(ApiErrorCodes.class)
public @interface ApiErrorCode {

    /** HTTP 状态码，如 "404" */
    String code();

    /** 错误场景说明 */
    String description();
}
