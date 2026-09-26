package com.hcsy.spring.infra.filter;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.mock.http.server.reactive.MockServerHttpRequest;
import org.springframework.mock.web.server.MockServerWebExchange;
import org.springframework.web.server.WebFilterChain;

import static org.mockito.Mockito.*;

import reactor.test.StepVerifier;

class SwaggerIndexRedirectWebFilterTest {
    // 验证该场景的预期行为
    @Test
    @DisplayName("Swagger 首页重定向到标准入口")
    void redirectsSwaggerIndex() {
        var exchange = MockServerWebExchange.from(MockServerHttpRequest.get("/swagger-ui/index.html").build());
        WebFilterChain chain = mock(WebFilterChain.class);
        StepVerifier.create(new SwaggerIndexRedirectWebFilter().filter(exchange, chain)).verifyComplete();
        org.junit.jupiter.api.Assertions.assertEquals(302, exchange.getResponse().getStatusCode().value());
        verifyNoInteractions(chain);
    }
}
