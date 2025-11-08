package com.hcsy.spring.common.annotation;

import java.lang.annotation.*;

/**
 * 文章同步注解，用于标记需要同步到MQ、ES、Hive和Vector的方法
 */
@Target({ ElementType.METHOD })
@Retention(RetentionPolicy.RUNTIME)
@Documented
public @interface ArticleSync {

    /**
     * 操作类型：add(新增)、edit(编辑)、delete(删除)、publish(发布)、view(浏览)
     */
    String action();

    /**
     * 操作描述信息
     */
    String description() default "";
}
