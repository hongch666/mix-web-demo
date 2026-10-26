package com.hcsy.spring.entity.vo;

import static org.junit.jupiter.api.Assertions.assertTrue;

import java.time.LocalDateTime;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;

/**
 * 用户同步视图序列化测试
 * 该 VO 替换了原先的匿名 Map，必须保持下划线字段名以兼容 FastAPI 与 GoZero 的解析
 */
class UserSyncVOTest {

    private final ObjectMapper objectMapper = new ObjectMapper().registerModule(new JavaTimeModule());

    // 验证该场景的预期行为
    @Test
    @DisplayName("按下划线字段序列化")
    void userSyncVoUsesSnakeCaseFields() throws Exception {
        UserSyncVO user = new UserSyncVO(
            1L, "tester", "t@example.com", "user", "img", "sig",
            LocalDateTime.now(), LocalDateTime.now());

        String userJson = objectMapper.writeValueAsString(user);

        assertTrue(userJson.contains("\"created_at\""));
        assertTrue(userJson.contains("\"updated_at\""));
    }
}
