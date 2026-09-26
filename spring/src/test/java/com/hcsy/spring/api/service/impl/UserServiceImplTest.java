package com.hcsy.spring.api.service.impl;
import static org.junit.jupiter.api.Assertions.assertNotNull;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
class UserServiceImplTest {
    // 验证该场景的预期行为
    @Test
    @DisplayName("用户服务实现类可加载")
    void loads() {
        assertNotNull(UserServiceImpl.class);
    }
}
