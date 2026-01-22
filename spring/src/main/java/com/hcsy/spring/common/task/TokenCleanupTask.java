package com.hcsy.spring.common.task;

import com.hcsy.spring.api.service.TokenService;
import com.hcsy.spring.common.utils.Constants;
import com.hcsy.spring.common.utils.SimpleLogger;

import lombok.RequiredArgsConstructor;

import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

@Component
@RequiredArgsConstructor
public class TokenCleanupTask {

    private final TokenService tokenService;
    private final SimpleLogger logger;

    /**
     * 定时清理过期的 Token
     * 每小时执行一次（在每个整点时刻）
     */
    @Scheduled(cron = "0 0 * * * *")
    public void cleanupExpiredTokens() {
        logger.info(Constants.TASK_START);
        try {
            tokenService.cleanupExpiredTokens();
            logger.info(Constants.TASK_END);
        } catch (Exception e) {
            logger.error(Constants.TASK_EXCEPTION + e.getMessage());
        }
    }
}
