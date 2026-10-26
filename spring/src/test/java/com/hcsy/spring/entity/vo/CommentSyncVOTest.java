package com.hcsy.spring.entity.vo;

import static org.junit.jupiter.api.Assertions.assertTrue;

import java.time.LocalDateTime;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;

/**
 * 评论同步视图序列化测试
 * 该 VO 替换了原先的匿名 Map，必须保持下划线字段名以兼容 FastAPI 与 GoZero 的解析
 */
class CommentSyncVOTest {

    private final ObjectMapper objectMapper = new ObjectMapper().registerModule(new JavaTimeModule());

    // 验证该场景的预期行为
    @Test
    @DisplayName("按下划线字段序列化")
    void commentSyncVoUsesSnakeCaseFields() throws Exception {
        CommentSyncVO comment = new CommentSyncVO(
            9L, 1L, 7L, 8.0, LocalDateTime.now(), LocalDateTime.now());

        String commentJson = objectMapper.writeValueAsString(comment);

        assertTrue(commentJson.contains("\"user_id\":1"));
        assertTrue(commentJson.contains("\"article_id\":7"));
        assertTrue(commentJson.contains("\"create_time\""));
    }
}
