package com.hcsy.spring.infra.client;

import java.io.IOException;
import java.time.Duration;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.web.reactive.function.client.ClientRequest;
import org.springframework.web.reactive.function.client.ClientResponse;
import org.springframework.web.reactive.function.client.ExchangeFunction;
import org.springframework.web.reactive.function.client.WebClient;

import com.hcsy.spring.common.constants.HeaderNames;
import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.utils.InternalTokenUtil;
import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.common.utils.UserContext;
import com.hcsy.spring.core.properties.ServiceClientProperties;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import io.github.resilience4j.circuitbreaker.CircuitBreakerRegistry;
import io.github.resilience4j.retry.RetryConfig;
import io.github.resilience4j.retry.RetryRegistry;
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;
import reactor.util.context.Context;

class ServiceWebClientTest {

    // 验证该场景的预期行为

    @Test
    @DisplayName("远程调用透传用户上下文并生成内部 Token")
    void propagatesContextHeadersAndInternalToken() {
        AtomicReference<ClientRequest> captured = new AtomicReference<>();
        ExchangeFunction exchange = request -> {
            captured.set(request);
            return Mono.just(jsonResponse("{\"code\":200,\"message\":\"ok\",\"data\":{}}"));
        };
        InternalTokenUtil tokenUtil = mock(InternalTokenUtil.class);
        when(tokenUtil.generateInternalToken(7L, "spring")).thenReturn("internal-token");
        ServiceWebClient client = createClient(exchange, tokenUtil, RetryRegistry.ofDefaults());

        Mono<Result<?>> response = client.request(
            HttpMethod.GET, "fastapi", "/health", ServiceRequestOptions.empty(), "fallback")
            .contextWrite(Context.of(
                UserContext.CONTEXT_KEY_USER_ID, 7L,
                UserContext.CONTEXT_KEY_USERNAME, "alice"));

        StepVerifier.create(response)
            .assertNext(result -> assertEquals(HttpCode.OK, result.getCode()))
            .verifyComplete();

        assertEquals("http://fastapi/health", captured.get().url().toString());
        assertEquals("7", captured.get().headers().getFirst(HeaderNames.USER_ID));
        assertEquals("alice", captured.get().headers().getFirst(HeaderNames.USERNAME));
        assertEquals("Bearer internal-token", captured.get().headers().getFirst("X-Internal-Token"));
        verify(tokenUtil).generateInternalToken(7L, "spring");
    }

    // 验证该场景的预期行为

    @Test
    @DisplayName("未登录系统调用使用 userId=-1 的内部 Token")
    void generatesSystemInternalTokenWithoutUserContext() {
        InternalTokenUtil tokenUtil = mock(InternalTokenUtil.class);
        when(tokenUtil.generateInternalToken(-1L, "spring")).thenReturn("system-token");
        ServiceWebClient client = createClient(
            request -> Mono.just(jsonResponse("{\"code\":200,\"message\":\"ok\",\"data\":null}")),
            tokenUtil,
            RetryRegistry.ofDefaults());

        StepVerifier.create(client.request(
            HttpMethod.GET, "fastapi", "/health", ServiceRequestOptions.empty(), "fallback"))
            .expectNextCount(1)
            .verifyComplete();

        verify(tokenUtil).generateInternalToken(-1L, "spring");
    }

    // 验证该场景的预期行为

    @Test
    @DisplayName("瞬时 IO 异常按配置重试并在耗尽后返回降级结果")
    void retriesIoFailureThenReturnsFallback() {
        AtomicInteger attempts = new AtomicInteger();
        ExchangeFunction exchange = request -> {
            attempts.incrementAndGet();
            return Mono.error(new IOException("temporary"));
        };
        RetryConfig retryConfig = RetryConfig.custom()
            .maxAttempts(3)
            .waitDuration(Duration.ZERO)
            .retryExceptions(IOException.class)
            .build();
        InternalTokenUtil tokenUtil = mock(InternalTokenUtil.class);
        when(tokenUtil.generateInternalToken(anyLong(), anyString())).thenReturn("token");
        SimpleLogger logger = mock(SimpleLogger.class);
        ServiceWebClient client = createClient(exchange, tokenUtil, RetryRegistry.of(retryConfig), logger);

        StepVerifier.create(client.request(
            HttpMethod.GET, "fastapi", "/health", ServiceRequestOptions.empty(), "service unavailable"))
            .assertNext(result -> {
                assertEquals(HttpCode.SERVICE_UNAVAILABLE, result.getCode());
                assertTrue(result.getMsg().contains("service unavailable"));
            })
            .verifyComplete();

        assertEquals(3, attempts.get());
        verify(logger).error(anyString(), org.mockito.ArgumentMatchers.any(Throwable.class));
    }

    private ServiceWebClient createClient(
        ExchangeFunction exchange,
        InternalTokenUtil tokenUtil,
        RetryRegistry retryRegistry) {
        return createClient(exchange, tokenUtil, retryRegistry, mock(SimpleLogger.class));
    }

    private ServiceWebClient createClient(
        ExchangeFunction exchange,
        InternalTokenUtil tokenUtil,
        RetryRegistry retryRegistry,
        SimpleLogger logger) {
        WebClient.Builder builder = WebClient.builder().exchangeFunction(exchange);
        return new ServiceWebClient(
            builder,
            tokenUtil,
            logger,
            CircuitBreakerRegistry.ofDefaults(),
            retryRegistry,
            new ServiceClientProperties(Duration.ofSeconds(1)));
    }

    private ClientResponse jsonResponse(String body) {
        return ClientResponse.create(HttpStatus.OK)
            .header("Content-Type", MediaType.APPLICATION_JSON_VALUE)
            .body(body)
            .build();
    }
}
