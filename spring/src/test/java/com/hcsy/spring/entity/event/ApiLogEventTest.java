package com.hcsy.spring.entity.event;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import com.fasterxml.jackson.databind.ObjectMapper;

/**
 * 接口日志事件序列化契约测试
 * 事件体会被 NestJS 消费者按固定字段解析，键名不能漂移，空字段不进入消息
 */
class ApiLogEventTest {

    private final ObjectMapper objectMapper = new ObjectMapper();

    // 验证该场景的预期行为
    @Test
    @DisplayName("忽略空字段且保留约定键名")
    void serializesApiLogEvent() throws Exception {
        ApiLogEvent event = ApiLogEvent.builder()
            .userId(0L)
            .username("unknown")
            .apiDescription("创建文章")
            .apiPath("/articles/{id}")
            .apiMethod("POST")
            .responseTime(12L)
            .build();

        String json = objectMapper.writeValueAsString(event);

        assertTrue(json.contains("\"apiDescription\":\"创建文章\""));
        assertTrue(json.contains("\"apiPath\":\"/articles/{id}\""));
        assertTrue(json.contains("\"responseTime\":12"));
        assertFalse(json.contains("pathParams"));
        assertFalse(json.contains("requestBody"));
        assertFalse(json.contains("queryParams"));
    }
}
