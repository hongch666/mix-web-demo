package com.hcsy.spring.api.service.impl;

import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

/** 服务实现契约测试，确保每个服务实现都有对应的公开业务方法 */
class ServiceImplementationsTest {
    // 验证该场景的预期行为
    @Test
    @DisplayName("所有服务实现均实现接口")
    void implementationsExposeBusinessMethods() {
        Class<?>[] implementations = {
            ArticleCollectServiceImpl.class,
            ArticleLikeServiceImpl.class,
            ArticleServiceImpl.class,
            AsyncApiLogServiceImpl.class,
            AsyncSyncServiceImpl.class,
            CategoryReferenceServiceImpl.class,
            CategoryServiceImpl.class,
            CommentsServiceImpl.class,
            EmailVerificationServiceImpl.class,
            FocusServiceImpl.class,
            ImageCaptchaServiceImpl.class,
            SqlToolsServiceImpl.class,
            SubCategoryServiceImpl.class,
            TokenServiceImpl.class,
            UserServiceImpl.class,
            WarehouseSyncServiceImpl.class
        };
        for (Class<?> implementation : implementations) {
            assertTrue(implementation.getInterfaces().length > 0, implementation.getSimpleName());
        }
    }
}
