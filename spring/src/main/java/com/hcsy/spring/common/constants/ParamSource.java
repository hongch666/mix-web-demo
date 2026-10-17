package com.hcsy.spring.common.constants;

/**
 * 权限注解的参数来源
 * 决定切面从控制器的哪类入参中提取目标资源标识
 */
public enum ParamSource {

    /** 路径中的单个参数，如 /articles/{id} */
    PATH_SINGLE,

    /** 路径中的多个参数，如 /articles/{articleId}/comments/{commentId} */
    PATH_MULTI,

    /** 请求体中的属性，如 ArticleUpdateDTO */
    BODY,

    /** 查询参数，如 ?user_id=1 */
    QUERY
}
