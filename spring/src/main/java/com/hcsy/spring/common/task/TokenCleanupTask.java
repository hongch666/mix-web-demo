package com.hcsy.spring.common.task;

import com.hcsy.spring.api.service.TokenService;
import com.hcsy.spring.common.utils.SimpleLogger;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

@Component
public class TokenCleanupTask {

    @Autowired
    private TokenService tokenService;

    @Autowired
    private SimpleLogger logger;

    /**
     * 定时清理过期的 Token
     * 每小时执行一次（在每个整点时刻）
     */
    @Scheduled(cron = "0 0 * * * *")
    public void cleanupExpiredTokens() {
        logger.info("开始执行定时清理过期 Token 任务");
        try {
            tokenService.cleanupExpiredTokens();
            logger.info("定时清理过期 Token 任务执行完成");
        } catch (Exception e) {
            logger.error("定时清理过期 Token 任务执行异常: " + e.getMessage());
        }
    }
}
