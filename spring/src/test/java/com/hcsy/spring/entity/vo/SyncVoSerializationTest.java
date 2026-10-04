package com.hcsy.spring.entity.vo;

import static org.junit.jupiter.api.Assertions.assertTrue;

import java.time.LocalDateTime;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;

/**
 * 同步视图对象序列化测试
 * 这些 VO 替换了原先的匿名 Map，必须保持下划线字段名以兼容 FastAPI 与 GoZero 的解析
 */
class SyncVoSerializationTest {

    private final ObjectMapper objectMapper = new ObjectMapper().registerModule(new JavaTimeModule());

    @Test
    @DisplayName("文章同步视图按下划线字段序列化")
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

    @Test
    @DisplayName("关系与评论同步视图按下划线字段序列化")
    void relationAndCommentVoUseSnakeCaseFields() throws Exception {
        ArticleRelationSyncVO relation = new ArticleRelationSyncVO(1L, 7L, LocalDateTime.now());
        String relationJson = objectMapper.writeValueAsString(relation);
        assertTrue(relationJson.contains("\"user_id\":1"));
        assertTrue(relationJson.contains("\"article_id\":7"));
        assertTrue(relationJson.contains("\"created_time\""));

        CommentSyncVO comment = new CommentSyncVO(
            9L, 1L, 7L, 8.0, LocalDateTime.now(), LocalDateTime.now());
        String commentJson = objectMapper.writeValueAsString(comment);
        assertTrue(commentJson.contains("\"user_id\":1"));
        assertTrue(commentJson.contains("\"article_id\":7"));
        assertTrue(commentJson.contains("\"create_time\""));
    }

    @Test
    @DisplayName("用户与分类同步视图按下划线字段序列化")
    void userAndCategoryVoUseSnakeCaseFields() throws Exception {
        UserSyncVO user = new UserSyncVO(
            1L, "tester", "t@example.com", "user", "img", "sig",
            LocalDateTime.now(), LocalDateTime.now());
        String userJson = objectMapper.writeValueAsString(user);
        assertTrue(userJson.contains("\"created_at\""));
        assertTrue(userJson.contains("\"updated_at\""));

        SubCategorySyncVO subCategory = new SubCategorySyncVO(2L, "子类", 3L, LocalDateTime.now());
        String subCategoryJson = objectMapper.writeValueAsString(subCategory);
        assertTrue(subCategoryJson.contains("\"category_id\":3"));
        assertTrue(subCategoryJson.contains("\"update_time\""));
    }
}
