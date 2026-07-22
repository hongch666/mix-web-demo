package com.hcsy.spring.infra.client;

import java.time.Duration;

import org.springframework.http.HttpMethod;
import org.springframework.stereotype.Component;

import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.utils.Result;

import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;

@Component
@RequiredArgsConstructor
public class FastAPIClient {

    private final ServiceWebClient serviceWebClient;

    public Mono<Result<?>> syncVector() {
        return serviceWebClient.request(HttpMethod.POST, "fastapi", "/task/vector", ServiceRequestOptions.empty(),
                Duration.ofSeconds(30),
                Messages.VECTOR_SYNC_SERVICE_UNAVAILABLE);
    }

    public Mono<Result<?>> clearAnalyzeCaches() {
        return serviceWebClient.request(HttpMethod.POST, "fastapi", "/task/clear-analyze-caches",
                ServiceRequestOptions.empty(), Duration.ofSeconds(30),
                Messages.ANALYSIS_CACHE_CLEANUP_SERVICE_UNAVAILABLE);
    }

    public Mono<Result<?>> syncNeo4j() {
        return serviceWebClient.request(HttpMethod.POST, "fastapi", "/task/sync-neo4j", ServiceRequestOptions.empty(),
                Duration.ofSeconds(30),
                Messages.NEO4J_SYNC_SERVICE_UNAVAILABLE);
    }
}
