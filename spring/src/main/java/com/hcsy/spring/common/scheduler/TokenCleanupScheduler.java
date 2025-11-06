package com.hcsy.spring.common.scheduler;

import com.hcsy.spring.api.service.TokenService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Token 清理定时任务
 * 每小时执行一次，清理所有过期的 Token
 */
@Component
public class TokenCleanupScheduler {
    private static final Logger logger = LoggerFactory.getLogger(TokenCleanupScheduler.class);

    @Autowired
    private TokenService tokenService;

    /**
     * 每小时执行一次
     * cron 表达式：0 0 * * * * 表示每小时的第 0 分钟执行
     */
    @Scheduled(cron = "0 0 * * * *")
    public void cleanupExpiredTokens() {
        try {
            logger.info("========== 开始执行 Token 清理定时任务 ==========");
            tokenService.cleanupExpiredTokens();
            logger.info("========== Token 清理定时任务执行完成 ==========");
        } catch (Exception e) {
            logger.error("Token 清理定时任务执行失败", e);
        }
    }

    /**
     * 也可以提供一个手动清理的方法（用于测试或紧急情况）
     * 可以通过管理员接口调用
     */
    public void manualCleanup() {
        logger.info("手动触发 Token 清理任务");
        tokenService.cleanupExpiredTokens();
    }
}