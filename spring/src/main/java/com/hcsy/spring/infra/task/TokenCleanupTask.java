package com.hcsy.spring.infra.task;

import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import com.hcsy.spring.api.service.TokenService;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.constants.Defaults;
import com.hcsy.spring.common.utils.RedisDistributedLock;
import com.hcsy.spring.common.utils.SimpleLogger;

import lombok.RequiredArgsConstructor;

@Component
@RequiredArgsConstructor
public class TokenCleanupTask {

    private final TokenService tokenService;
    private final SimpleLogger logger;
    private final RedisDistributedLock distributedLock;

    /**
     * 定时清理过期的 Token
     * 每小时执行一次（在每个整点时刻）
     * 使用 Redis 分布式锁，保证多实例部署时只有一个实例执行
     */
    @Scheduled(cron = "0 0 * * * *")
    public void cleanupExpiredTokens() {
        String lockKey = Defaults.LOCK_TASK_TOKEN_CLEANUP;
        String lockValue = distributedLock.tryLock(lockKey, Defaults.LOCK_TASK_TOKEN_CLEANUP_EXPIRE);
        if (lockValue == null) {
            logger.info(String.format(Messages.LOCK_ACQUIRE_FAIL, lockKey));
            return;
        }
        logger.info(String.format(Messages.LOCK_ACQUIRE_SUCCESS, lockKey));
        try {
            logger.info(Messages.TASK_START);
            tokenService.cleanupExpiredTokens();
            logger.info(Messages.TASK_END);
        } catch (Exception e) {
            logger.error(Messages.TASK_EXCEPTION + e.getMessage());
        } finally {
            boolean released = distributedLock.unlock(lockKey, lockValue);
            if (released) {
                logger.info(String.format(Messages.LOCK_RELEASE_SUCCESS, lockKey));
            } else {
                logger.warning(String.format(Messages.LOCK_RELEASE_FAIL, lockKey));
            }
        }
    }
}
