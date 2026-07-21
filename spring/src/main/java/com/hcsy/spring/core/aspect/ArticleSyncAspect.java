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
import com.hcsy.spring.common.utils.UserContextHolder;
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
            // Controller 层返回 Mono 的方法：在响应式链内获取 Reactor Context
            return monoResult
                .flatMap(res -> Mono.deferContextual(ctx -> {
                    executeSync(joinPoint, articleSync, ctx);
                    return Mono.just(res);
                }));
        }

        // Service 层返回非 Mono 类型的方法（boolean/Long/void 等）：
        // 这些方法在 Controller 的 Mono.deferContextual 内同步调用，
        // 不在响应式链中，需要直接执行同步逻辑
        executeSync(joinPoint, articleSync, null);
        return result;
    }

    /**
     * 执行同步逻辑：发送 MQ 消息 + 触发 ES/Vector 同步
     *
     * @param ctx Reactor Context，非 Mono 路径传入 null（会从 ThreadLocal 回退读取）
     */
    private void executeSync(ProceedingJoinPoint joinPoint, ArticleSync articleSync,
            reactor.util.context.ContextView ctx) {
        try {
            String action = articleSync.action();
            String description = articleSync.description();
            Object[] paramValues = joinPoint.getArgs();

            Map<String, Object> msg = new HashMap<>();
            Map<String, Object> content = new HashMap<>();

            // 优先从 Reactor Context 读取，非 Mono 路径回退到 ThreadLocal
            Long userId;
            String username;
            if (ctx != null) {
                userId = UserContext.getUserId(ctx);
                username = UserContext.getUsername(ctx);
            } else {
                userId = UserContextHolder.getUserId();
                username = UserContextHolder.getUsername();
            }

            // 根据注解类型构建消息
            buildActionMessage(action, paramValues, content, msg, userId, description);
            msg.put("action", action);

            // 发送消息
            String json = objectMapper.writeValueAsString(msg);
            rabbitMQUtil.sendMessage("article-log-queue", msg);
            logger.info(Messages.MQ_SEND + json);

            // 触发异步同步 ES 和 Vector
            asyncSyncService.syncAllAsync(userId, username);
        } catch (Exception e) {
            logger.error(Messages.TRANSACTION_ROLLBACK + e.getMessage());
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

        // 公共处理逻辑
        msg.put("content", content);
        msg.put("userId", userId);
    }
}
