package com.hcsy.spring.application.sync.annotation;

import java.lang.annotation.Documented;
import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

import com.hcsy.spring.common.constants.SyncAction;
import com.hcsy.spring.common.constants.SyncResource;

/**
 * 文章同步注解，用于标记需要同步到 MQ、ES、Neo4j、Hive 和 Vector 的接口方法
 * 只加在控制器方法上，切面在业务成功后统一触发同步
 */
@Target({ ElementType.METHOD })
@Retention(RetentionPolicy.RUNTIME)
@Documented
public @interface ArticleSync {

    /**
     * 操作类型，见 SyncAction
     */
    SyncAction action();

    /**
     * 资源名，精确同步时下发给下游用于定位源表，默认为文章
     */
    String resource() default SyncResource.ARTICLES;

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
