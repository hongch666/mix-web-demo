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
     * 业务类型：user, article, comment, category, subcategory 等
     */
    String businessType() default "user";

    /**
     * 参数来源：path_single, path_multi, body
     * path_single: 路径单个参数如 /users/{id}
     * path_multi: 路径多个参数如 /article/{articleId}/comment/{commentId}
     * body: 请求体中的参数如 UserUpdateDTO
     */
    String paramSource() default "path_single";

    /**
     * 参数名称（可以是路径参数名或请求体属性名）
     * 如 id, articleId, commentId, username 等
     */
    String[] paramNames() default { "id" };
}