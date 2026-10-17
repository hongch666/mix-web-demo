package com.hcsy.spring.common.constants;

/**
 * 权限校验的业务资源类型
 * 决定归属校验时查询哪个资源表，由应用服务的归属校验组件按类型分发
 */
public enum BusinessType {

    /** 用户自身，目标标识即用户 ID */
    USER,

    /** 文章，归属字段为文章作者 */
    ARTICLE,

    /** 评论，归属字段为评论作者 */
    COMMENT,

    /** 分类，仅做角色校验，无个人归属语义 */
    CATEGORY,

    /** 子分类，仅做角色校验，无个人归属语义 */
    SUB_CATEGORY,

    /** 分类权威参考文本，仅做角色校验，无个人归属语义 */
    CATEGORY_REFERENCE
}
