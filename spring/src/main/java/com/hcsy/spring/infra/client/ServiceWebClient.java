package com.hcsy.spring.infra.client;

import java.net.URI;
import java.time.Duration;
import java.util.List;
import java.util.Map;

import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.util.MultiValueMap;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.util.UriBuilder;

import com.hcsy.spring.common.constants.HeaderNames;
import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.utils.InternalTokenUtil;
import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.common.utils.UserContext;
import com.hcsy.spring.core.properties.ServiceClientProperties;

import io.github.resilience4j.circuitbreaker.CircuitBreakerRegistry;
import io.github.resilience4j.reactor.circuitbreaker.operator.CircuitBreakerOperator;
import io.github.resilience4j.reactor.retry.RetryOperator;
import io.github.resilience4j.retry.RetryRegistry;
import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;

@Component
@RequiredArgsConstructor
public class ServiceWebClient {

    private static final String INTERNAL_TOKEN_HEADER = "X-Internal-Token";
    private static final String USER_ID_HEADER = HeaderNames.USER_ID;
    private static final String USERNAME_HEADER = HeaderNames.USERNAME;
    private static final String BEARER_PREFIX = "Bearer ";
    private static final String SERVICE_NAME = "spring";
    private static final ParameterizedTypeReference<Result<Object>> RESULT_TYPE = new ParameterizedTypeReference<>() {
    };

    private final WebClient.Builder webClientBuilder;
    private final InternalTokenUtil internalTokenUtil;
    private final SimpleLogger logger;
    private final CircuitBreakerRegistry circuitBreakerRegistry;
    private final RetryRegistry retryRegistry;
    private final ServiceClientProperties serviceClientProperties;

    /**
     * 使用配置中的统一超时时间发起请求
     */
    public Mono<Result<?>> request(
        HttpMethod method,
        String serviceName,
        String path,
        ServiceRequestOptions options,
        String fallbackMessage) {
        return request(method, serviceName, path, options,
            serviceClientProperties.timeout(), fallbackMessage);
    }

    public Mono<Result<?>> request(
        HttpMethod method,
        String serviceName,
        String path,
        ServiceRequestOptions options,
        Duration timeout,
        String fallbackMessage) {
        ServiceRequestOptions requestOptions = options == null ? ServiceRequestOptions.empty() : options;

        // 获取对应服务的熔断器和重试器
        var circuitBreaker = circuitBreakerRegistry.circuitBreaker(serviceName);
        var retry = retryRegistry.retry(serviceName);

        return Mono.deferContextual(context -> {
            Long userId = UserContext.getUserId(context);
            String username = UserContext.getUsername(context);
            String token = internalTokenUtil.generateInternalToken(userId == null ? -1L : userId, SERVICE_NAME);

            WebClient.RequestBodySpec request = webClientBuilder.build()
                .method(method)
                .uri(uriBuilder -> buildUri(
                    uriBuilder, serviceName, path, requestOptions.getQueryParameters(),
                    requestOptions.getPathVariables()))
                .headers(requestHeaders -> applyHeaders(
                    requestHeaders, requestOptions.getHeaders(), userId, username, token));
            WebClient.RequestHeadersSpec<?> requestSpec = requestOptions.getBody() == null
                ? request
                : request.bodyValue(requestOptions.getBody());
            return requestSpec
                .retrieve()
                .bodyToMono(RESULT_TYPE)
                .cast(Result.class)
                .map(result -> (Result<?>) result)
                .timeout(timeout)
                // 应用重试机制
                .transformDeferred(RetryOperator.of(retry))
                // 应用熔断机制
                .transformDeferred(CircuitBreakerOperator.of(circuitBreaker))
                .onErrorResume(error -> {
                    logger.error(fallbackMessage + error.getMessage(), error);
                    return Mono.just(Result.error(HttpCode.SERVICE_UNAVAILABLE, fallbackMessage));
                });
        });
    }

    private URI buildUri(
        UriBuilder uriBuilder,
        String serviceName,
        String path,
        MultiValueMap<String, String> queryParameters,
        Map<String, ?> pathVariables) {
        UriBuilder target = uriBuilder
            .scheme("http")
            .host(serviceName)
            .path(normalizePath(path));
        if (queryParameters != null) {
            queryParameters.forEach((name, values) -> addQueryParameter(target, name, values));
        }
        return target.build(pathVariables == null ? Map.of() : pathVariables);
    }

    private void addQueryParameter(UriBuilder uriBuilder, String name, List<String> values) {
        if (values == null || values.isEmpty()) {
            uriBuilder.queryParam(name);
            return;
        }
        uriBuilder.queryParam(name, values.toArray());
    }

    private void applyHeaders(
        HttpHeaders requestHeaders,
        HttpHeaders customHeaders,
        Long userId,
        String username,
        String internalToken) {
        if (customHeaders != null) {
            requestHeaders.addAll(customHeaders);
        }

        requestHeaders.setAccept(List.of(MediaType.APPLICATION_JSON));
        requestHeaders.set(INTERNAL_TOKEN_HEADER, BEARER_PREFIX + internalToken);
        setOrRemove(requestHeaders, USER_ID_HEADER, userId == null ? null : userId.toString());
        setOrRemove(requestHeaders, USERNAME_HEADER, username);
    }

    private void setOrRemove(HttpHeaders headers, String name, String value) {
        if (value == null) {
            headers.remove(name);
            return;
        }
        headers.set(name, value);
    }

    private String normalizePath(String path) {
        return path.startsWith("/") ? path : "/" + path;
    }
}
