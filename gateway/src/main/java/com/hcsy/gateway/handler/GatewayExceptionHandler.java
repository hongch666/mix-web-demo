package com.hcsy.gateway.handler;

import java.net.ConnectException;
import java.util.concurrent.TimeoutException;

import org.springframework.boot.web.reactive.error.ErrorWebExceptionHandler;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.http.server.reactive.ServerHttpResponse;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;

import com.hcsy.gateway.common.BusinessException;
import com.hcsy.gateway.common.Constants;
import com.hcsy.gateway.common.HttpCode;
import com.hcsy.gateway.common.Result;

import lombok.extern.slf4j.Slf4j;
import reactor.core.publisher.Mono;

@Component
@Order(Ordered.HIGHEST_PRECEDENCE)
@Slf4j
public class GatewayExceptionHandler implements ErrorWebExceptionHandler {

    @SuppressWarnings("null")
    @Override
    public Mono<Void> handle(ServerWebExchange exchange, Throwable ex) {
        if (exchange.getResponse().isCommitted()) {
            return Mono.error(ex);
        }

        ServerHttpResponse response = exchange.getResponse();

        // BusinessException - 业务异常，使用其自带的状态码和消息
        if (ex instanceof BusinessException biz) {
            response.setStatusCode(org.springframework.http.HttpStatus.valueOf(biz.getStatusCode()));
            log.error("[{}] 业务异常 - 路径: {}", biz.getError(), exchange.getRequest().getPath(), biz);
            return Result.error(biz.getStatusCode(), biz.getMessage()).writeTo(response);
        }

        // NotFoundException - Spring Cloud Gateway 找不到可用服务实例（503）
        if (isNotFoundException(ex)) {
            response.setStatusCode(org.springframework.http.HttpStatus.SERVICE_UNAVAILABLE);
            String serviceId = extractServiceId(ex.getMessage());
            String msg = serviceId != null
                    ? String.format("找不到可用的服务实例: %s", serviceId)
                    : "服务不可用";
            log.error("[{}] 路径: {}", Constants.NO_AVAILABLE_SERVICE_INSTANCE, exchange.getRequest().getPath(), ex);
            return Result.error(HttpCode.SERVICE_UNAVAILABLE, msg).writeTo(response);
        }

        // ConnectException - 下游服务连接失败（502）
        if (isConnectException(ex)) {
            response.setStatusCode(org.springframework.http.HttpStatus.BAD_GATEWAY);
            log.error("[{}] 服务调用失败 - 路径: {}", Constants.SERVICE_CALL_FAILED, exchange.getRequest().getPath(), ex);
            return Result.error(HttpCode.BAD_GATEWAY, "服务调用失败").writeTo(response);
        }

        // TimeoutException - 请求超时（504）
        if (isTimeoutException(ex)) {
            response.setStatusCode(org.springframework.http.HttpStatus.GATEWAY_TIMEOUT);
            log.error("[{}] 请求超时 - 路径: {}", Constants.REQUEST_TIMEOUT, exchange.getRequest().getPath(), ex);
            return Result.error(HttpCode.GATEWAY_TIMEOUT, "请求超时，请稍后重试").writeTo(response);
        }

        // 其他异常 - 服务器内部错误（500）
        response.setStatusCode(org.springframework.http.HttpStatus.INTERNAL_SERVER_ERROR);
        log.error("[{}] 网关内部错误 - 路径: {}", Constants.GATEWAY_SERVER_ERROR, exchange.getRequest().getPath(), ex);
        return Result.error(HttpCode.INTERNAL_SERVER_ERROR, Constants.DEFAULT_ERROR_MSG).writeTo(response);
    }

    /**
     * 判断是否为 NotFoundException（Spring Cloud Gateway 的服务发现异常）
     */
    private boolean isNotFoundException(Throwable ex) {
        return ex.getClass().getName().equals("org.springframework.cloud.gateway.support.NotFoundException");
    }

    /**
     * 判断是否为连接异常（下游服务不可达）
     */
    private boolean isConnectException(Throwable ex) {
        Throwable current = ex;
        while (current != null) {
            if (current instanceof ConnectException) {
                return true;
            }
            current = current.getCause();
        }
        return false;
    }

    /**
     * 判断是否为超时异常
     */
    private boolean isTimeoutException(Throwable ex) {
        Throwable current = ex;
        while (current != null) {
            if (current instanceof TimeoutException) {
                return true;
            }
            // Spring Cloud Gateway 的响应超时异常
            String className = current.getClass().getName();
            if (className.contains("TimeoutException") || className.contains("ReadTimeoutException")) {
                return true;
            }
            current = current.getCause();
        }
        return false;
    }

    /**
     * 从 NotFoundException 消息中提取服务ID
     * 消息格式: "Unable to find instance for spring"
     */
    private String extractServiceId(String message) {
        if (message == null) {
            return null;
        }
        String prefix = "Unable to find instance for ";
        int idx = message.indexOf(prefix);
        if (idx >= 0) {
            String serviceId = message.substring(idx + prefix.length()).trim();
            // 去除可能的引号
            return serviceId.replace("\"", "");
        }
        return null;
    }
}
