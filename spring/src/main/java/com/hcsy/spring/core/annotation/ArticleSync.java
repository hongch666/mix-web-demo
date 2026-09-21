package com.hcsy.spring.core.annotation;

import java.lang.annotation.Documented;
import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

/**
 * 文章同步注解，用于标记需要同步到 MQ、ES、Neo4j、Hive 和 Vector 的接口方法
 * 只加在控制器方法上，切面在业务成功后统一触发同步
 */
@Target({ ElementType.METHOD })
@Retention(RetentionPolicy.RUNTIME)
@Documented
public @interface ArticleSync {

    /**
     * 操作类型：add(新增)、edit(编辑)、delete(删除)、publish(发布)、view(浏览)、like(点赞)、unlike(取消点赞)、
     * collect(收藏)、uncollect(取消收藏)、focus(关注)、unfocus(取消关注)
     */
    String action();

    /**
     * 操作描述信息
     */
    String description() default "";

    /**
     * 是否触发 ES 同步
     * ES 中的浏览量、点赞数、收藏数、关注数在检索时由 Spring 回填，仅参与排序，
     * 因此浏览、点赞、收藏、关注等不改变文章文档的操作无需同步 ES
     */
    boolean esSync() default false;

    /**
     * 是否触发向量库同步
     * 只有可能改变文章内容的操作才需要打开，浏览、点赞、收藏、关注等不涉及文章内容的操作保持关闭
     */
    boolean vectorSync() default false;
}
