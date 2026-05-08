package com.hcsy.spring.core.annotation;

import java.lang.annotation.Documented;
import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

/**
 * Neo4j 同步注解，用于标记需要在方法成功后触发知识图谱同步的入口
 */
@Target({ ElementType.METHOD })
@Retention(RetentionPolicy.RUNTIME)
@Documented
public @interface Neo4jSync {

    /**
     * 操作描述，用于日志记录
     */
    String description() default "";
}
