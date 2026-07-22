package com.hcsy.spring.infra.client;

import java.util.Map;

import org.springframework.http.HttpHeaders;
import org.springframework.util.MultiValueMap;

import lombok.Builder;
import lombok.Getter;

/**
 * 微服务请求的可选参数。
 */
@Getter
@Builder
public class ServiceRequestOptions {

    private HttpHeaders headers;
    private Object body;
    private MultiValueMap<String, String> queryParameters;
    private Map<String, ?> pathVariables;

    public static ServiceRequestOptions empty() {
        return ServiceRequestOptions.builder().build();
    }
}
