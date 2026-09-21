package com.hcsy.spring.core.aspect;

import java.util.Arrays;
import java.util.Collection;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.springframework.stereotype.Component;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.hcsy.spring.api.service.AsyncSyncService;
import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.utils.RabbitMQUtil;
import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.common.utils.UserContext;
import com.hcsy.spring.core.annotation.ArticleSync;

import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;
import reactor.util.context.Context;

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
            // 使用 doOnSuccess 发后即忘：主流程不等待 MQ 发送和 ES/向量库/数仓/图谱同步完成
            return Mono.deferContextual(ctx -> {
                Long userId = UserContext.getUserId(ctx);
                String username = UserContext.getUsername(ctx);
                Context syncContext = UserContext.writeContext(Context.empty(), userId, username, null, null, null);
                return monoResult.doOnSuccess(res -> {
                    if (isBusinessSuccess(res)) {
                        executeSync(joinPoint, articleSync, userId, username)
                            .contextWrite(syncContext)
                            .subscribe();
                    }
                });
            });
        }
        return result;
    }

    /**
     * 判断业务结果是否成功，只有真正发生数据变更才触发同步
     * 控制器在业务失败时会返回携带错误码的 Result，这类结果不能触发同步
     */
    private boolean isBusinessSuccess(Object result) {
        if (result instanceof Result<?> businessResult) {
            return businessResult.getCode() != null && businessResult.getCode() == HttpCode.OK;
        }
        return true;
    }

    /**
     * 执行同步逻辑：发送 MQ 消息 + 触发 ES/向量库/数仓/Neo4j 同步
     */
    private Mono<Void> executeSync(ProceedingJoinPoint joinPoint, ArticleSync articleSync,
        Long userId, String username) {
        try {
            String action = articleSync.action();
            String description = articleSync.description();
            Object[] paramValues = joinPoint.getArgs();

            Map<String, Object> msg = new HashMap<>();
            Map<String, Object> content = new HashMap<>();

            // 根据注解类型构建消息
            buildActionMessage(action, paramValues, content, msg, userId, description);
            msg.put("action", action);

            // 发送消息到 MQ + 触发 ES/向量库/数仓/图谱同步，并行执行
            String json = objectMapper.writeValueAsString(msg);
            return Mono.whenDelayError(
                rabbitMQUtil.sendMessage("article-log-queue", msg)
                    .doOnSuccess(ignored -> logger.info(Messages.MQ_SEND + json)),
                asyncSyncService.syncAllAsync(userId, username, articleSync.esSync(), articleSync.vectorSync()),
                asyncSyncService.syncNeo4jAsync(joinPoint.getSignature().toShortString(), description))
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
     * 注解作用在控制器上，入参可能是 DTO、路径变量或逗号分隔的 ID 字符串，统一按属性名解析
     */
    private void buildActionMessage(String action, Object[] paramValues, Map<String, Object> content,
        Map<String, Object> msg, Long userId, String description) {
        Object primaryParam = paramValues.length > 0 ? paramValues[0] : null;

        switch (action) {
            case "add":
            case "edit": {
                Long articleId = readLong(primaryParam, "id");
                content.put("id", articleId);
                content.put("title", readString(primaryParam, "title"));
                content.put("tags", readString(primaryParam, "tags"));
                msg.put("articleId", articleId);
                msg.put("msg", description);
                break;
            }
            case "delete": {
                List<Long> ids = readIds(primaryParam);
                if (ids.size() > 1) {
                    content.put("ids", ids);
                    msg.put("articleIds", ids);
                    msg.put("msg", description + ids.size() + "篇文章");
                } else {
                    Long id = ids.isEmpty() ? null : ids.get(0);
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
                Long id = readRelatedId(primaryParam);
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

    /**
     * 按属性名读取对象值，兼容控制器入参的 DTO 与实体
     */
    private Object readProperty(Object target, String property) {
        if (target == null) {
            return null;
        }
        try {
            String getterName = "get" + Character.toUpperCase(property.charAt(0)) + property.substring(1);
            return target.getClass().getMethod(getterName).invoke(target);
        } catch (ReflectiveOperationException e) {
            return null;
        }
    }

    /**
     * 读取 Long 类型属性，属性不存在时返回 null
     */
    private Long readLong(Object target, String property) {
        Object value = readProperty(target, property);
        return value instanceof Number number ? number.longValue() : null;
    }

    /**
     * 读取 String 类型属性，属性不存在时返回 null
     */
    private String readString(Object target, String property) {
        Object value = readProperty(target, property);
        return value instanceof String text ? text : null;
    }

    /**
     * 解析删除接口的文章 ID 集合，兼容单个 ID、ID 集合和逗号分隔的 ID 字符串
     */
    private List<Long> readIds(Object target) {
        if (target instanceof Number number) {
            return List.of(number.longValue());
        }
        if (target instanceof Collection<?> collection) {
            return collection.stream()
                .filter(Number.class::isInstance)
                .map(item -> ((Number) item).longValue())
                .toList();
        }
        if (target instanceof String text) {
            return Arrays.stream(text.split(","))
                .map(String::trim)
                .filter(item -> !item.isEmpty())
                .map(Long::valueOf)
                .toList();
        }
        Long id = readLong(target, "id");
        return id == null ? List.of() : List.of(id);
    }

    /**
     * 解析关联 ID：点赞、收藏取文章 ID，关注取发起用户 ID
     */
    private Long readRelatedId(Object target) {
        if (target instanceof Number number) {
            return number.longValue();
        }
        Long articleId = readLong(target, "articleId");
        return articleId != null ? articleId : readLong(target, "userId");
    }
}
