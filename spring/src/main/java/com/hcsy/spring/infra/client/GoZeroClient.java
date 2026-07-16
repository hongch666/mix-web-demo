package com.hcsy.spring.infra.client;

import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;

import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.infra.client.fallback.GoZeroClientFallbackFactory;

@FeignClient(name = "gozero", fallbackFactory = GoZeroClientFallbackFactory.class)
public interface GoZeroClient {
    @GetMapping("/api_gozero/gozero")
    Result<?> testGoZero();

    @PostMapping("/api_gozero/syncer")
    Result<?> syncES();

    // 手动触发文章向量同步 (pgvector 均值 → ES embedding_vector)
    @PostMapping("/api_gozero/syncer/embedding")
    Result<?> syncEmbedding();

    // 手动触发表谱特征缓存同步 (Neo4j → Redis)
    @PostMapping("/api_gozero/syncer/graph-cache")
    Result<?> syncGraphCache();
}
