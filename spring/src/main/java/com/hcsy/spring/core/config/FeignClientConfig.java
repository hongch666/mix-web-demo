package com.hcsy.spring.core.config;

import java.io.IOException;
import java.lang.reflect.Type;
import java.nio.charset.StandardCharsets;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.hcsy.spring.common.utils.Constants;
import com.hcsy.spring.common.utils.HttpCode;
import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.common.utils.SimpleLogger;

import feign.FeignException;
import feign.Response;
import feign.codec.Decoder;
import lombok.RequiredArgsConstructor;

/**
 * Feign 客户端全局配置
 * 提供业务响应码校验，当响应 code != 200 时抛出异常触发 FallbackFactory
 */
@Configuration
@RequiredArgsConstructor
public class FeignClientConfig {

    private final ObjectMapper objectMapper;
    private final SimpleLogger logger;

    @Bean
    public Decoder feignDecoder() {
        return new Decoder() {
            @SuppressWarnings("rawtypes")
            @Override
            public Object decode(Response response, Type type) throws IOException, FeignException {
                // 读取完整响应体
                String body = "";
                if (response.body() != null) {
                    body = new String(response.body().asInputStream().readAllBytes(), StandardCharsets.UTF_8);
                }

                // 解析业务码，校验是否成功
                if (!body.isEmpty()) {
                    try {
                        Result result = objectMapper.readValue(body, Result.class);
                        if (result.getCode() != null && result.getCode() != HttpCode.OK) {
                            String msg = result.getMsg() != null ? result.getMsg() : Constants.FEIGN_UNKNOWN_ERROR;
                            logger.error(
                                    Constants.FEIGN_BUSINESS_ERROR_LOG,
                                    result.getCode(),
                                    msg);
                            throw new RuntimeException(Constants.FEIGN_CALL_FAIL + msg);
                        }
                    } catch (RuntimeException e) {
                        throw e;
                    } catch (Exception e) {
                        logger.warning(Constants.FEIGN_PARSE_WARNING + e.getMessage());
                    }
                }

                // 使用 ObjectMapper 反序列化为目标类型
                if (body.isEmpty()) {
                    return null;
                }
                try {
                    return objectMapper.readValue(body, objectMapper.constructType(type));
                } catch (Exception e) {
                    logger.error(Constants.FEIGN_DESERIALIZE_FAIL + e.getMessage());
                    throw new RuntimeException(Constants.FEIGN_DESERIALIZE_FAIL + e.getMessage());
                }
            }
        };
    }
}
