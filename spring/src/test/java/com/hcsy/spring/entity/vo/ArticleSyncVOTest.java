package com.hcsy.spring.entity.vo;

import static org.junit.jupiter.api.Assertions.assertTrue;

import java.time.LocalDateTime;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;

/**
 * 文章同步视图序列化测试
 * 该 VO 替换了原先的匿名 Map，必须保持下划线字段名以兼容 FastAPI 与 GoZero 的解析
 */
class ArticleSyncVOTest {

    private final ObjectMapper objectMapper = new ObjectMapper().registerModule(new JavaTimeModule());

    // 验证该场景的预期行为
    @Test
    @DisplayName("按下划线字段序列化")
    void articleSyncVoUsesSnakeCaseFields() throws Exception {
        ArticleSyncVO vo = new ArticleSyncVO(
            7L, "标题", "内容", 1L, "go", 1, 3, 2,
            LocalDateTime.of(2026, 1, 1, 0, 0), LocalDateTime.of(2026, 1, 2, 0, 0));

        String json = objectMapper.writeValueAsString(vo);

        assertTrue(json.contains("\"user_id\":1"));
        assertTrue(json.contains("\"sub_category_id\":2"));
        assertTrue(json.contains("\"create_at\""));
        assertTrue(json.contains("\"update_at\""));
    }
}
