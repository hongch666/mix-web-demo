package com.hcsy.spring.infra.filter;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.mock.http.server.reactive.MockServerHttpRequest;
import org.springframework.mock.web.server.MockServerWebExchange;
import org.springframework.web.server.WebFilterChain;

import com.hcsy.spring.common.constants.HeaderNames;
import com.hcsy.spring.common.utils.UserContext;

import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

class UserContextWebFilterTest {
    // 验证该场景的预期行为
    @Test
    @DisplayName("请求头写入 Reactor 用户上下文")
    void writesContext() {
        var request = MockServerHttpRequest.get("/").header(HeaderNames.USER_ID, "7")
            .header(HeaderNames.USERNAME, "alice").header("Authorization", "Bearer access").build();
        var exchange = MockServerWebExchange.from(request);
        WebFilterChain chain = ex -> Mono.deferContextual(ctx -> {
            org.junit.jupiter.api.Assertions.assertEquals(7L, UserContext.getUserId(ctx));
            org.junit.jupiter.api.Assertions.assertEquals("access", UserContext.getToken(ctx));
            return Mono.empty();
        });
        StepVerifier.create(new UserContextWebFilter().filter(exchange, chain)).verifyComplete();
    }
}
