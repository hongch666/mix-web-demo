package com.hcsy.spring.core.annotation;

import java.lang.annotation.Documented;
import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

/**
 * 数据同步注解，用于标记方法成功后需要触发下游数据同步的入口
 * 当前覆盖 Neo4j 图谱同步与 ClickHouse 数仓同步，凡会改变图谱关系或数仓统计口径的写操作都应标注
 * 文章相关的同步链路（MQ 日志、ES、向量库）由 ArticleSync 注解负责，二者职责不同
 */
@Target({ ElementType.METHOD })
@Retention(RetentionPolicy.RUNTIME)
@Documented
public @interface DataSync {

    /**
     * 操作描述，用于日志记录
     */
    String description() default "";
}
