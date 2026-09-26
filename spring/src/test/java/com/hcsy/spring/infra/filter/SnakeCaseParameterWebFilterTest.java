package com.hcsy.spring.infra.filter;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.mock.http.server.reactive.MockServerHttpRequest;
import org.springframework.mock.web.server.MockServerWebExchange;
import org.springframework.web.server.WebFilterChain;

import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

class SnakeCaseParameterWebFilterTest {
    // 验证该场景的预期行为
    @Test
    @DisplayName("查询参数补充驼峰别名")
    void addsCamelCaseQueryAlias() {
        var exchange = MockServerWebExchange.from(MockServerHttpRequest.get("/?user_id=7").build());
        WebFilterChain chain = ex -> {
            assertEquals("7", ex.getRequest().getQueryParams().getFirst("userId"));
            return Mono.empty();
        };
        StepVerifier.create(new SnakeCaseParameterWebFilter().filter(exchange, chain)).verifyComplete();
    }
}
