package com.hcsy.gateway.common;

import org.springframework.core.io.buffer.DataBuffer;
import org.springframework.http.MediaType;
import org.springframework.http.server.reactive.ServerHttpResponse;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import reactor.core.publisher.Mono;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Slf4j
public class Result {
    private Integer code;
    private String msg;
    private Object data;

    private static final ObjectMapper OBJECT_MAPPER = new ObjectMapper();

    public static Result success() {
        return new Result(HttpCode.OK, "success", null);
    }

    public static Result success(Object data) {
        return new Result(HttpCode.OK, "success", data);
    }

    public static Result error(String msg) {
        return new Result(HttpCode.INTERNAL_SERVER_ERROR, msg, null);
    }

    public static Result error(int code, String msg) {
        return new Result(code, msg, null);
    }

    /**
     * 将当前 Result 写入 ServerHttpResponse 并返回 Mono<Void>
     */
    @SuppressWarnings("null")
    public Mono<Void> writeTo(ServerHttpResponse response) {
        response.getHeaders().setContentType(MediaType.APPLICATION_JSON);
        try {
            byte[] bytes = OBJECT_MAPPER.writeValueAsBytes(this);
            DataBuffer buffer = response.bufferFactory().wrap(bytes);
            return response.writeWith(Mono.just(buffer));
        } catch (JsonProcessingException e) {
            log.error("序列化响应结果失败", e);
            return response.setComplete();
        }
    }
}
