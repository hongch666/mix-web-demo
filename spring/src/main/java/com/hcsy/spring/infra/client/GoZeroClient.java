package com.hcsy.spring.infra.client;

import org.springframework.http.HttpMethod;
import org.springframework.stereotype.Component;

import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.entity.event.ChangeEvent;

import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;

@Component
@RequiredArgsConstructor
public class GoZeroClient {

    private final ServiceWebClient serviceWebClient;

    public Mono<Result<?>> syncES(ChangeEvent event) {
        return serviceWebClient.request(HttpMethod.POST, "gozero", "/task/syncer",
            ServiceRequestOptions.builder().body(event).build(), Messages.ES_SERVICE_UNAVAILABLE);
    }
}
