package com.hcsy.spring.infra.client;

import java.util.List;
import java.util.Map;
import java.util.Set;

import org.springframework.http.HttpMethod;
import org.springframework.stereotype.Component;

import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.entity.event.ChangeEvent;

import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;

/**
 * 封装对 FastAPI 服务的调用，提供向量库、数仓与 Neo4j 数据同步接口
 */
@Component
@RequiredArgsConstructor
public class FastAPIClient {

    private final ServiceWebClient serviceWebClient;

    /**
     * 调用 FastAPI 服务的向量同步接口，将数据变更事件下发到向量库
     */
    public Mono<Result<?>> syncVector(ChangeEvent event) {
        return serviceWebClient.request(HttpMethod.POST, "fastapi", "/task/vector",
            ServiceRequestOptions.builder().body(event).build(), Messages.VECTOR_SYNC_SERVICE_UNAVAILABLE);
    }

    /**
     * 调用 FastAPI 服务的数仓同步接口，按资源名集合触发数仓数据同步
     */
    public Mono<Result<?>> syncWarehouse(Set<String> resources) {
        return serviceWebClient.request(HttpMethod.POST, "fastapi", "/task/sync-warehouse",
            ServiceRequestOptions.builder()
                .body(Map.of("resources", resources == null ? List.of() : List.copyOf(resources)))
                .build(),
            Messages.WAREHOUSE_SYNC_SERVICE_UNAVAILABLE);
    }

    /**
     * 调用 FastAPI 服务的 Neo4j 同步接口，批量下发数据变更事件到图数据库
     */
    public Mono<Result<?>> syncNeo4j(List<ChangeEvent> events) {
        return serviceWebClient.request(HttpMethod.POST, "fastapi", "/task/sync-neo4j",
            ServiceRequestOptions.builder()
                .body(Map.of("events", events == null ? List.of() : events))
                .build(),
            Messages.NEO4J_SYNC_SERVICE_UNAVAILABLE);
    }
}
