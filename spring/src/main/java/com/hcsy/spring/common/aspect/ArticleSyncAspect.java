package com.hcsy.spring.common.aspect;

import lombok.RequiredArgsConstructor;
import org.aspectj.lang.annotation.*;

import java.util.HashMap;
import java.util.Map;
import java.util.List;

import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.reflect.MethodSignature;
import org.springframework.stereotype.Component;
import org.springframework.transaction.support.TransactionSynchronization;
import org.springframework.transaction.support.TransactionSynchronizationManager;
import org.springframework.transaction.support.TransactionTemplate;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.hcsy.spring.common.annotation.ArticleSync;
import com.hcsy.spring.common.exceptions.BusinessException;
import com.hcsy.spring.common.utils.Constants;
import com.hcsy.spring.common.utils.RabbitMQUtil;
import com.hcsy.spring.api.service.AsyncSyncService;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.common.utils.UserContext;
import com.hcsy.spring.entity.po.Article;

@Aspect
@Component
@RequiredArgsConstructor
public class ArticleSyncAspect {

    private final RabbitMQUtil rabbitMQUtil;
    private final ObjectMapper objectMapper;
    private final TransactionTemplate transactionTemplate;
    private final SimpleLogger logger;
    private final AsyncSyncService asyncSyncService;

    @Pointcut("@annotation(com.hcsy.spring.common.annotation.ArticleSync)")
    public void articleSyncMethods() {
    }

    @Around("articleSyncMethods()")
    public Object handleArticleSync(ProceedingJoinPoint joinPoint) throws Throwable {
        return transactionTemplate.execute(status -> {
            try {
                // 1. 执行业务方法（写数据库）
                Object result = joinPoint.proceed();

                // 2. 获取注解信息和方法元数据
                MethodSignature methodSignature = (MethodSignature) joinPoint.getSignature();
                ArticleSync articleSync = methodSignature.getMethod().getAnnotation(ArticleSync.class);

                if (articleSync == null) {
                    return result;
                }

                String action = articleSync.action();
                String description = articleSync.description();
                Object[] paramValues = joinPoint.getArgs();

                Map<String, Object> msg = new HashMap<>();
                Map<String, Object> content = new HashMap<>();

                // 3. 获取当前用户 ID
                Long userId = UserContext.getUserId();

                // 4. 根据注解类型构建消息
                buildActionMessage(action, paramValues, content, msg, userId, description);
                msg.put("action", action);

                // 5. 发送消息
                String json = objectMapper.writeValueAsString(msg);
                rabbitMQUtil.sendMessage("log-queue", msg);
                logger.info(Constants.MQ_SEND + json);

                // 6. 在主线程中保存用户信息，用于异步任务日志记录
                final Long currentUserId = userId;
                final String currentUsername = UserContext.getUsername();

                // 7. 注册事务提交后的回调，异步同步 ES、Hive 和 Vector
                TransactionSynchronizationManager.registerSynchronization(new TransactionSynchronization() {
                    @Override
                    public void afterCommit() {
                        logger.info(Constants.TRIGGER_SYNC);
                        // 根据操作类型选择不同的同步策略
                        if ("like".equals(action) || "unlike".equals(action) || "collect".equals(action)
                                || "uncollect".equals(action) || "focus".equals(action) || "unfocus".equals(action)) {
                            // 点赞、取消点赞、收藏、取消收藏、关注、取消关注操作不同步
                            logger.info(Constants.UNSYNC_TYPE);
                        } else if ("view".equals(action)) {
                            // 浏览量操作只同步 Hive
                            asyncSyncService.syncHiveOnlyAsync(currentUserId, currentUsername);
                        } else {
                            // 其他操作同步 ES、Hive 和 Vector
                            asyncSyncService.syncAllAsync(currentUserId, currentUsername);
                        }
                    }
                });

                return result;

            } catch (Throwable e) {
                logger.error(Constants.TRANSACTION_ROLLBACK + e.getMessage());
                status.setRollbackOnly(); // 显式回滚
                throw new BusinessException(Constants.TRANSACTION_ROLLBACK);
            }
        });
    }

    /**
     * 根据操作类型构建消息内容
     */
    private void buildActionMessage(String action, Object[] paramValues, Map<String, Object> content,
            Map<String, Object> msg, Long userId, String description) {
        switch (action) {
            case "add":
            case "edit": {
                Article article = (Article) paramValues[0];
                content.put("id", article.getId());
                content.put("title", article.getTitle());
                content.put("tags", article.getTags());
                msg.put("article_id", article.getId());
                msg.put("msg", description);
                break;
            }
            case "delete": {
                if (paramValues[0] instanceof List) {
                    @SuppressWarnings("unchecked")
                    List<Long> ids = (List<Long>) paramValues[0];
                    content.put("ids", ids);
                    msg.put("article_ids", ids);
                    msg.put("msg", description + ids.size() + "篇文章");
                } else {
                    Long id = (Long) paramValues[0];
                    content.put("id", id);
                    msg.put("article_id", id);
                    msg.put("msg", description);
                }
                break;
            }
            case "publish":
            case "view":
            case "like":
            case "unlike":
            case "collect":
            case "uncollect":
            case "focus":
            case "unfocus": {
                Long id = (Long) paramValues[0];
                content.put("id", id);
                msg.put("article_id", id);
                msg.put("msg", description);
                break;
            }
            default:
                logger.error(Constants.UNKNOWN_OPERATION + action);
                throw new BusinessException(Constants.UNKNOWN_OPERATION);
        }

        // 公共处理逻辑
        msg.put("content", content);
        msg.put("user_id", userId);
    }
}