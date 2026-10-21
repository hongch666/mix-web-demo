package com.hcsy.spring.infra.client;

import org.springframework.http.HttpMethod;
import org.springframework.stereotype.Component;

import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.entity.event.ChangeEvent;

import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;

/**
 * 封装对 GoZero 服务的调用，将数据变更事件同步到 Elasticsearch
 */
@Component
@RequiredArgsConstructor
public class GoZeroClient {

    private final ServiceWebClient serviceWebClient;

    /**
     * 调用 GoZero 服务的 ES 同步接口，将数据变更事件下发到 Elasticsearch
     */
    public Mono<Result<?>> syncES(ChangeEvent event) {
        return serviceWebClient.request(HttpMethod.POST, "gozero", "/task/syncer",
            ServiceRequestOptions.builder().body(event).build(), Messages.ES_SERVICE_UNAVAILABLE);
    }
}
