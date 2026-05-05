package com.hcsy.gateway.filter;

import java.util.List;

import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.cloud.gateway.filter.GlobalFilter;
import org.springframework.core.Ordered;
import org.springframework.http.HttpStatus;
import org.springframework.http.server.reactive.ServerHttpResponse;
import org.springframework.stereotype.Component;
import org.springframework.util.AntPathMatcher;
import org.springframework.web.server.ServerWebExchange;

import com.hcsy.gateway.common.HttpCode;
import com.hcsy.gateway.common.Result;
import com.hcsy.gateway.config.AuthProperties;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import reactor.core.publisher.Mono;

@Component
@RequiredArgsConstructor
@Slf4j
public class ExcludeListGlobalFilter implements GlobalFilter, Ordered {

  private final AuthProperties authProperties;
  private final AntPathMatcher antPathMatcher = new AntPathMatcher();

  @SuppressWarnings("null")
  @Override
  public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
    String path = exchange.getRequest().getPath().toString();

    List<String> blockPatterns = authProperties.getBlockPaths();
    if (blockPatterns == null || blockPatterns.isEmpty()) {
      return chain.filter(exchange);
    }

    boolean matched = blockPatterns.stream()
        .anyMatch(pattern -> antPathMatcher.match(pattern, path));

    if (!matched) {
      return chain.filter(exchange);
    }

    log.info("排除列表拦截路径: {}", path);
    ServerHttpResponse response = exchange.getResponse();
    response.setStatusCode(HttpStatus.FORBIDDEN);
    return Result.error(HttpCode.FORBIDDEN, "该接口为内部接口，仅内部使用").writeTo(response);
  }

  @Override
  public int getOrder() {
    return -50;
  }
}
