package com.hcsy.spring.entity.event;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.List;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import com.hcsy.spring.common.constants.SyncAction;
import com.hcsy.spring.common.constants.SyncChangeType;
import com.hcsy.spring.common.constants.SyncResource;

import com.fasterxml.jackson.databind.ObjectMapper;

/**
 * 队列消息序列化契约测试
 * 消息体会被 NestJS 消费者按固定字段解析，字段名与枚举取值不能漂移
 */
class EventMessageSerializationTest {

    private final ObjectMapper objectMapper = new ObjectMapper();

    @Test
    @DisplayName("文章日志按约定输出字符串 action 并忽略未使用字段")
    void serializesArticleLogMessage() throws Exception {
        ArticleLogMessage message = ArticleLogMessage.builder()
            .action(SyncAction.ADD)
            .resource(SyncResource.ARTICLES)
            .changeType(SyncChangeType.INSERT.value())
            .msg("创建了1篇文章")
            .userId(7L)
            .articleId(21L)
            .content(ArticleLogMessage.Content.builder().id(21L).title("标题").build())
            .build();

        String json = objectMapper.writeValueAsString(message);

        assertTrue(json.contains("\"action\":\"add\""));
        assertTrue(json.contains("\"changeType\":\"insert\""));
        assertTrue(json.contains("\"articleId\":21"));
        assertTrue(json.contains("\"content\":{\"id\":21,\"title\":\"标题\"}"));
        assertFalse(json.contains("articleIds"));
        assertFalse(json.contains("tags"));
    }

    @Test
    @DisplayName("文章日志批量删除输出 articleIds 与 content.ids")
    void serializesArticleLogBatchDelete() throws Exception {
        ArticleLogMessage message = ArticleLogMessage.builder()
            .action(SyncAction.DELETE)
            .articleIds(List.of(21L, 22L))
            .content(ArticleLogMessage.Content.builder().ids(List.of(21L, 22L)).build())
            .build();

        String json = objectMapper.writeValueAsString(message);

        assertTrue(json.contains("\"action\":\"delete\""));
        assertTrue(json.contains("\"articleIds\":[21,22]"));
        assertTrue(json.contains("\"content\":{\"ids\":[21,22]}"));
        assertFalse(json.contains("articleId\":"));
    }

    @Test
    @DisplayName("接口日志忽略空字段且保留约定键名")
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
