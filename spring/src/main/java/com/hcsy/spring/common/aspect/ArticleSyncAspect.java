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
import com.hcsy.spring.common.mq.RabbitMQService;
import com.hcsy.spring.api.service.AsyncSyncService;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.common.utils.UserContext;
import com.hcsy.spring.entity.po.Article;

@Aspect
@Component
@RequiredArgsConstructor
public class ArticleSyncAspect {

    private final RabbitMQService rabbitMQService;
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
                rabbitMQService.sendMessage("log-queue", json);
                logger.info("发送到MQ：" + json);

                // 6. 在主线程中保存用户信息，用于异步任务日志记录
                final Long currentUserId = userId;
                final String currentUsername = UserContext.getUsername();

                // 7. 注册事务提交后的回调，异步同步 ES、Hive 和 Vector
                TransactionSynchronizationManager.registerSynchronization(new TransactionSynchronization() {
                    @Override
                    public void afterCommit() {
                        logger.info("事务提交后触发异步同步任务...");
                        // 根据操作类型选择不同的同步策略
                        if ("like".equals(action) || "unlike".equals(action) || "collect".equals(action)
                                || "uncollect".equals(action)) {
                            // 点赞、取消点赞、收藏、取消收藏操作不同步
                            logger.info("点赞/收藏类操作不同步");
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
                logger.error("事务执行失败，已回滚", e);
                status.setRollbackOnly(); // 显式回滚
                throw new RuntimeException(e);
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
            case "uncollect": {
                Long id = (Long) paramValues[0];
                content.put("id", id);
                msg.put("article_id", id);
                msg.put("msg", description);
                break;
            }
            default:
                logger.error("未知操作类型：" + action);
                throw new RuntimeException("AOP识别失败：未知的操作类型");
        }

        // 公共处理逻辑
        msg.put("content", content);
        msg.put("user_id", userId);
    }
}