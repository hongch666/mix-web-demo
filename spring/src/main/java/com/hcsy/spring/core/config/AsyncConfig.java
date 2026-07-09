package com.hcsy.spring.core.config;

import java.util.concurrent.Executor;
import java.util.concurrent.ThreadPoolExecutor;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;

/**
 * 异步任务配置
 * 用于后台异步执行耗时操作（如同步 ES、Hive、Vector、邮件发送等）
 */
@Configuration
@EnableAsync
public class AsyncConfig {
    /**
     * API 日志异步发送执行器
     * 用于异步发送 API 日志到 RabbitMQ，不阻塞业务接口响应
     */
    @Bean(name = "apiLogExecutor")
    Executor apiLogExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        // 核心线程数（API 日志发送是高频后台任务）
        executor.setCorePoolSize(3);
        // 最大线程数
        executor.setMaxPoolSize(6);
        // 队列容量
        executor.setQueueCapacity(200);
        // 线程名前缀
        executor.setThreadNamePrefix("api-log-sender-");
        // 拒绝策略：由调用线程处理（保证日志不丢失）
        executor.setRejectedExecutionHandler(new ThreadPoolExecutor.CallerRunsPolicy());
        // 等待所有任务结束后再关闭线程池
        executor.setWaitForTasksToCompleteOnShutdown(true);
        // 最长等待时间（秒）
        executor.setAwaitTerminationSeconds(30);
        executor.initialize();
        return executor;
    }

    /**
     * 后台同步任务执行器
     * 用于 ES/Vector/Neo4j 等后台同步任务，与用户请求线程池隔离
     * 注意：syncAllAsync 内部会再 spawn 3 个 CompletableFuture 子任务，
     * 因此单次调用最多消耗 4 个线程，corePoolSize 需足够应对并发同步请求
     */
    @Bean(name = "syncTaskExecutor")
    Executor syncTaskExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        // 核心线程数（并发同步请求数 × 4 个子任务）
        executor.setCorePoolSize(4);
        // 最大线程数
        executor.setMaxPoolSize(12);
        // 队列容量（后台同步不需要大缓冲，满了就 CallerRuns 兜底）
        executor.setQueueCapacity(50);
        // 线程名前缀
        executor.setThreadNamePrefix("sync-task-");
        // 拒绝策略：由调用线程处理（保证同步任务不丢失）
        executor.setRejectedExecutionHandler(new ThreadPoolExecutor.CallerRunsPolicy());
        // 等待所有任务结束后再关闭线程池
        executor.setWaitForTasksToCompleteOnShutdown(true);
        // 最长等待时间（秒）
        executor.setAwaitTerminationSeconds(60);
        executor.initialize();
        return executor;
    }

    /**
     * 用户查询并行执行器
     * 用于用户请求链路中的批量并行查询（如在线设备数），与后台同步任务隔离
     */
    @Bean(name = "userQueryExecutor")
    Executor userQueryExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        // 核心线程数
        executor.setCorePoolSize(5);
        // 最大线程数
        executor.setMaxPoolSize(10);
        // 队列容量
        executor.setQueueCapacity(100);
        // 线程名前缀
        executor.setThreadNamePrefix("user-query-");
        // 拒绝策略：由调用线程处理
        executor.setRejectedExecutionHandler(new ThreadPoolExecutor.CallerRunsPolicy());
        // 等待所有任务结束后再关闭线程池
        executor.setWaitForTasksToCompleteOnShutdown(true);
        // 最长等待时间（秒）
        executor.setAwaitTerminationSeconds(30);
        executor.initialize();
        return executor;
    }

    /**
     * 邮件发送异步执行器
     */
    @Bean(name = "taskExecutor")
    Executor taskExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        // 核心线程数
        executor.setCorePoolSize(3);
        // 最大线程数
        executor.setMaxPoolSize(8);
        // 队列容量
        executor.setQueueCapacity(50);
        // 线程名前缀
        executor.setThreadNamePrefix("mail-sender-");
        // 拒绝策略：由调用线程处理（确保邮件一定会被发送）
        executor.setRejectedExecutionHandler(new ThreadPoolExecutor.CallerRunsPolicy());
        // 等待所有任务结束后再关闭线程池
        executor.setWaitForTasksToCompleteOnShutdown(true);
        // 最长等待时间（秒）
        executor.setAwaitTerminationSeconds(60);
        executor.initialize();
        return executor;
    }
}
