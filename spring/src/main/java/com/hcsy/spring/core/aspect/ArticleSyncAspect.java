package com.hcsy.spring.core.aspect;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.springframework.stereotype.Component;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.hcsy.spring.api.service.AsyncSyncService;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.utils.RabbitMQUtil;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.common.utils.UserContext;
import com.hcsy.spring.core.annotation.ArticleSync;
import com.hcsy.spring.entity.po.Article;

import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;

@Aspect
@Component
@RequiredArgsConstructor
public class ArticleSyncAspect {

    private final RabbitMQUtil rabbitMQUtil;
    private final ObjectMapper objectMapper;
    private final SimpleLogger logger;
    private final AsyncSyncService asyncSyncService;

    @Around("@annotation(articleSync)")
    public Object handleArticleSync(ProceedingJoinPoint joinPoint, ArticleSync articleSync) throws Throwable {
        Object result = joinPoint.proceed();

        if (result instanceof Mono<?> monoResult) {
            // 使用 doOnSuccess 发后即忘：主流程不等待 MQ 发送和 ES/Vector 同步完成
            return monoResult
                .doOnSuccess(res -> {
                    Mono.deferContextual(ctx ->
                        executeSync(joinPoint, articleSync, ctx)
                    ).subscribe();
                });
        }
        return result;
    }

    /**
     * 执行同步逻辑：发送 MQ 消息 + 触发 ES/Vector 同步
     */
    private Mono<Void> executeSync(ProceedingJoinPoint joinPoint, ArticleSync articleSync,
            reactor.util.context.ContextView ctx) {
        try {
            String action = articleSync.action();
            String description = articleSync.description();
            Object[] paramValues = joinPoint.getArgs();

            Map<String, Object> msg = new HashMap<>();
            Map<String, Object> content = new HashMap<>();

            Long userId = UserContext.getUserId(ctx);
            String username = UserContext.getUsername(ctx);

            // 根据注解类型构建消息
            buildActionMessage(action, paramValues, content, msg, userId, description);
            msg.put("action", action);

            // 发送消息到 MQ + 触发 ES/Vector 同步，并行执行
            String json = objectMapper.writeValueAsString(msg);
            return Mono.whenDelayError(
                            rabbitMQUtil.sendMessage("article-log-queue", msg)
                                    .doOnSuccess(ignored -> logger.info(Messages.MQ_SEND + json)),
                            asyncSyncService.syncAllAsync(userId, username))
                    .onErrorResume(error -> {
                        logger.error(Messages.TRANSACTION_ROLLBACK + error.getMessage(), error);
                        return Mono.empty();
                    });
        } catch (Exception e) {
            logger.error(Messages.TRANSACTION_ROLLBACK + e.getMessage(), e);
            return Mono.empty();
        }
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
                msg.put("articleId", article.getId());
                msg.put("msg", description);
                break;
            }
            case "delete": {
                if (paramValues[0] instanceof List) {
                    @SuppressWarnings("unchecked")
                    List<Long> ids = (List<Long>) paramValues[0];
                    content.put("ids", ids);
                    msg.put("articleIds", ids);
                    msg.put("msg", description + ids.size() + "篇文章");
                } else {
                    Long id = (Long) paramValues[0];
                    content.put("id", id);
                    msg.put("articleId", id);
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
                msg.put("articleId", id);
                msg.put("msg", description);
                break;
            }
            default:
                logger.error(Messages.UNKNOWN_OPERATION + action);
                break;
        }

        msg.put("content", content);
        msg.put("userId", userId);
    }
}
