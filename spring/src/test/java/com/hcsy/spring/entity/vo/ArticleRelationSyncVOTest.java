package com.hcsy.spring.entity.vo;

import static org.junit.jupiter.api.Assertions.assertTrue;

import java.time.LocalDateTime;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;

/**
 * 文章关系同步视图序列化测试
 * 该 VO 替换了原先的匿名 Map，必须保持下划线字段名以兼容 FastAPI 与 GoZero 的解析
 */
class ArticleRelationSyncVOTest {

    private final ObjectMapper objectMapper = new ObjectMapper().registerModule(new JavaTimeModule());

    // 验证该场景的预期行为
    @Test
    @DisplayName("按下划线字段序列化")
    void relationSyncVoUsesSnakeCaseFields() throws Exception {
        ArticleRelationSyncVO relation = new ArticleRelationSyncVO(1L, 7L, LocalDateTime.now());

        String relationJson = objectMapper.writeValueAsString(relation);

        assertTrue(relationJson.contains("\"user_id\":1"));
        assertTrue(relationJson.contains("\"article_id\":7"));
        assertTrue(relationJson.contains("\"created_time\""));
    }
}
