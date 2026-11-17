package com.hcsy.spring.application.service;

import java.util.List;

import reactor.core.publisher.Mono;

/**
 * OSS 在用引用查询服务，供 NestJS 定时清理任务获取数据库里仍在使用的对象链接
 */
public interface OssReferenceService {

    /**
     * 查询 Spring 库中在用的 OSS 原始链接，去重后返回；对象 key 由调用方解析
     */
    Mono<List<String>> listOssReferenceUrls();
}
