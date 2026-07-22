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

import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.utils.InternalTokenUtil;
import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.common.utils.UserContext;

import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;

@Component
@RequiredArgsConstructor
public class ServiceWebClient {

    private static final String INTERNAL_TOKEN_HEADER = "X-Internal-Token";
    private static final String USER_ID_HEADER = "X-User-Id";
    private static final String USERNAME_HEADER = "X-Username";
    private static final String BEARER_PREFIX = "Bearer ";
    private static final String SERVICE_NAME = "spring";
    private static final ParameterizedTypeReference<Result<Object>> RESULT_TYPE = new ParameterizedTypeReference<>() {
    };

    private final WebClient.Builder webClientBuilder;
    private final InternalTokenUtil internalTokenUtil;
    private final SimpleLogger logger;

    @SuppressWarnings("null")
    public Mono<Result<?>> request(
            HttpMethod method,
            String serviceName,
            String path,
            ServiceRequestOptions options,
            Duration timeout,
            String fallbackMessage) {
        ServiceRequestOptions requestOptions = options == null ? ServiceRequestOptions.empty() : options;
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
                    .onErrorResume(error -> {
                        logger.error(fallbackMessage + error.getMessage(), error);
                        return Mono.just(Result.error(HttpCode.SERVICE_UNAVAILABLE, fallbackMessage));
                    });
        });
    }

    @SuppressWarnings("null")
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

    @SuppressWarnings("null")
    private void addQueryParameter(UriBuilder uriBuilder, String name, List<String> values) {
        if (values == null || values.isEmpty()) {
            uriBuilder.queryParam(name);
            return;
        }
        uriBuilder.queryParam(name, values.toArray());
    }

    @SuppressWarnings("null")
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

    @SuppressWarnings("null")
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
