package com.hcsy.spring.api.service;

import java.util.List;
import java.util.Map;

import reactor.core.publisher.Mono;

/**
 * SQL工具服务接口（供FastAPI Agent远程调用）
 * 提供受限的只读参数化SQL查询能力和表结构查询能力
 */
public interface SqlToolsService {

    /**
     * 获取表结构信息
     *
     * @param table
     *                  表名，为空则返回所有白名单表
     */
    Mono<List<Map<String, Object>>> getTables(String table);

    /**
     * 执行只读参数化SQL查询
     *
     * @param query
     *                   参数化SQL（使用 :paramName 占位符）
     * @param params
     *                   参数键值对
     */
    Mono<Map<String, Object>> executeQuery(String query, Map<String, Object> params);
}
