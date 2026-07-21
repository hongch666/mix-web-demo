package com.hcsy.spring.common.utils;

import java.util.List;
import java.util.concurrent.Callable;

import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.stereotype.Component;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import reactor.core.scheduler.Scheduler;

/**
 * 阻塞调用包装为响应式
 * 用于将 MyBatis-Plus 等阻塞式数据库操作包装为 Mono/Flux
 */
@Component
public class ReactiveWrapper {

    private final Scheduler jdbcScheduler;

    public ReactiveWrapper(@Qualifier("jdbcScheduler") Scheduler jdbcScheduler) {
        this.jdbcScheduler = jdbcScheduler;
    }

    /**
     * 包装单个阻塞调用为 Mono
     */
    public <T> Mono<T> wrap(Callable<T> blockingCall) {
        return Mono.fromCallable(blockingCall).subscribeOn(jdbcScheduler);
    }

    /**
     * 包装列表查询阻塞调用为 Flux
     */
    public <T> Flux<T> wrapList(Callable<List<T>> blockingCall) {
        return Mono.fromCallable(blockingCall).flatMapMany(Flux::fromIterable).subscribeOn(jdbcScheduler);
    }
}
