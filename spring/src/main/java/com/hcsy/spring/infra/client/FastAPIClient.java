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

@Component
@RequiredArgsConstructor
public class FastAPIClient {

    private final ServiceWebClient serviceWebClient;

    public Mono<Result<?>> syncVector(ChangeEvent event) {
        return serviceWebClient.request(HttpMethod.POST, "fastapi", "/task/vector",
            ServiceRequestOptions.builder().body(event).build(), Messages.VECTOR_SYNC_SERVICE_UNAVAILABLE);
    }

    public Mono<Result<?>> syncWarehouse(Set<String> resources) {
        return serviceWebClient.request(HttpMethod.POST, "fastapi", "/task/sync-warehouse",
            ServiceRequestOptions.builder()
                .body(Map.of("resources", resources == null ? List.of() : List.copyOf(resources)))
                .build(),
            Messages.WAREHOUSE_SYNC_SERVICE_UNAVAILABLE);
    }

    public Mono<Result<?>> syncNeo4j(List<ChangeEvent> events) {
        return serviceWebClient.request(HttpMethod.POST, "fastapi", "/task/sync-neo4j",
            ServiceRequestOptions.builder()
                .body(Map.of("events", events == null ? List.of() : events))
                .build(),
            Messages.NEO4J_SYNC_SERVICE_UNAVAILABLE);
    }
}
