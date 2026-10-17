package com.hcsy.spring.common.constants;

/**
 * RabbitMQ 队列名常量
 * 发送方与声明方共用同一份定义，避免队列名在各处硬编码后漂移
 */
public final class RabbitQueues {

    /** 接口日志队列，由 NestJS 消费后落 MongoDB */
    public static final String API_LOG = "api-log-queue";

    /** 文章日志队列，由 NestJS 消费后落 MongoDB 并供数仓同步 */
    public static final String ARTICLE_LOG = "article-log-queue";

    private RabbitQueues() {
    }
}
