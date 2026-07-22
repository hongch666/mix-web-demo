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
public class GoZeroClient {

    private final ServiceWebClient serviceWebClient;

    public Mono<Result<?>> syncES() {
        return serviceWebClient.request(HttpMethod.POST, "gozero", "/task/syncer", ServiceRequestOptions.empty(),
                Duration.ofSeconds(3),
                Messages.ES_SERVICE_UNAVAILABLE);
    }
}
