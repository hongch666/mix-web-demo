package com.hcsy.spring.web.sync.aspect;

import java.util.List;

import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.aspectj.lang.reflect.MethodSignature;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;

import com.hcsy.spring.application.service.AsyncSyncService;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.constants.RabbitQueues;
import com.hcsy.spring.common.constants.SyncAction;
import com.hcsy.spring.common.constants.SyncChangeType;
import com.hcsy.spring.common.utils.RabbitMQUtil;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.common.utils.SyncEventCollector;
import com.hcsy.spring.entity.event.ArticleLogMessage;
import com.hcsy.spring.entity.event.ChangeEvent;
import com.hcsy.spring.web.sync.annotation.ArticleSync;

import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;

/**
 * 文章同步切面
 * 在标注 @ArticleSync 的方法成功后并行触发 MQ 日志、ES、向量库与 Neo4j 同步
 */
@Aspect
@Component
@Order(30)
@RequiredArgsConstructor
public class ArticleSyncAspect extends AbstractSyncAspect<ArticleSync> {

    private final RabbitMQUtil rabbitMQUtil;
    private final ObjectMapper objectMapper;
    private final SimpleLogger logger;
    private final AsyncSyncService asyncSyncService;

    /**
     * 环绕通知，在标注 @ArticleSync 的接口成功执行后并行触发文章操作日志投递与ES、向量库、Neo4j同步
     */
    @Around("@annotation(articleSync)")
    public Object handleArticleSync(ProceedingJoinPoint joinPoint, ArticleSync articleSync) throws Throwable {
        return aroundSync(joinPoint, articleSync);
    }

    /**
     * 按操作类型解析受影响资源ID并构建日志消息与变更事件，并行投递MQ日志与各异步同步任务，失败仅记录日志不影响主流程
     */
    @Override
    protected Mono<Void> trigger(ProceedingJoinPoint joinPoint, ArticleSync articleSync, Object result,
        Long userId, String username) {
        try {
            Object[] paramValues = joinPoint.getArgs() == null ? new Object[0] : joinPoint.getArgs();
            List<Long> ids = resolveIds(joinPoint, articleSync.action(), paramValues, result);
            ArticleLogMessage message = buildMessage(joinPoint, articleSync, paramValues, userId, ids);

            ChangeEvent event = ChangeEvent.of(articleSync.resource(),
                SyncChangeType.fromAction(articleSync.action()), ids, articleSync.action().value());
            event.setTriggerUserId(userId);
            event.setTriggerUsername(username);

            String json = objectMapper.writeValueAsString(message);
            return Mono.whenDelayError(
                rabbitMQUtil.sendMessage(RabbitQueues.ARTICLE_LOG, message)
                    .doOnSuccess(ignored -> logger.info(Messages.MQ_SEND + json)),
                asyncSyncService.syncArticleAsync(userId, username, articleSync.esSync(), articleSync.vectorSync(),
                    event),
                asyncSyncService.syncNeo4jAsync(joinPoint.getSignature().toShortString(), articleSync.description(),
                    event))
                .onErrorResume(error -> {
                    logger.error(Messages.TRANSACTION_ROLLBACK + error.getMessage(), error);
                    return Mono.empty();
                });
        } catch (Exception error) {
            logger.error(Messages.TRANSACTION_ROLLBACK + error.getMessage(), error);
            return Mono.empty();
        }
    }

    /**
     * 按操作类型构建队列消息
     * 注解作用在控制器上，入参可能是 DTO、路径变量或逗号分隔的 ID 字符串，统一按属性名解析
     */
    private ArticleLogMessage buildMessage(ProceedingJoinPoint joinPoint, ArticleSync articleSync,
        Object[] paramValues, Long userId, List<Long> ids) {
        SyncAction action = articleSync.action();
        Object primaryParam = paramValues.length > 0 ? paramValues[0] : null;

        ArticleLogMessage.ArticleLogMessageBuilder builder = ArticleLogMessage.builder()
            .action(action)
            .resource(articleSync.resource())
            .changeType(SyncChangeType.fromAction(action).value())
            .msg(articleSync.description())
            .userId(userId);

        switch (action) {
            case ADD, EDIT -> builder
                .articleId(SyncEventCollector.readLong(primaryParam, "id"))
                .content(ArticleLogMessage.Content.builder()
                    .id(SyncEventCollector.readLong(primaryParam, "id"))
                    .title(SyncEventCollector.readString(primaryParam, "title"))
                    .tags(SyncEventCollector.readString(primaryParam, "tags"))
                    .build());
            case DELETE -> {
                if (ids.size() > 1) {
                    builder.articleIds(ids)
                        .msg(articleSync.description() + ids.size() + "篇文章")
                        .content(ArticleLogMessage.Content.builder().ids(ids).build());
                } else {
                    Long articleId = ids.isEmpty() ? null : ids.get(0);
                    builder.articleId(articleId)
                        .content(ArticleLogMessage.Content.builder().id(articleId).build());
                }
            }
            case PUBLISH, VIEW, LIKE, UNLIKE, COLLECT, UNCOLLECT -> {
                Long articleId = readArticleRelatedId(primaryParam);
                builder.articleId(articleId)
                    .content(ArticleLogMessage.Content.builder().id(articleId).build());
            }
            case FOCUS, UNFOCUS -> {
                Long targetUserId = resolveFocusTarget(joinPoint, primaryParam);
                // 关注与文章无关，articleId 传 -1 占位，与 GoZero 搜索日志的约定保持一致，双方用户 ID 放在 content 内，由数仓从 content 解析目标用户
                builder.articleId(-1L)
                    .content(ArticleLogMessage.Content.builder()
                        .id(targetUserId)
                        .sourceUserId(userId)
                        .targetUserId(targetUserId)
                        .build());
            }
        }
        return builder.build();
    }

    /**
     * 根据操作类型解析受影响主键
     * 新增取业务返回值中的新主键，编辑、发布、浏览取入参文章 ID，删除支持单个与批量
     */
    private List<Long> resolveIds(ProceedingJoinPoint joinPoint, SyncAction action, Object[] paramValues,
        Object result) {
        Object primaryParam = paramValues.length > 0 ? paramValues[0] : null;
        return switch (action) {
            case ADD -> SyncEventCollector.readIdsFromResult(result);
            case DELETE -> SyncEventCollector.readIds(primaryParam);
            case LIKE, UNLIKE, COLLECT, UNCOLLECT -> {
                Long articleId = readArticleRelatedId(primaryParam);
                yield articleId == null ? List.of() : List.of(articleId);
            }
            case FOCUS, UNFOCUS -> {
                Long targetUserId = resolveFocusTarget(joinPoint, primaryParam);
                yield targetUserId == null ? List.of() : List.of(targetUserId);
            }
            default -> {
                List<Long> directIds = SyncEventCollector.readIds(primaryParam);
                if (!directIds.isEmpty()) {
                    yield directIds;
                }
                Long id = readParameterId(joinPoint, "id");
                yield id == null ? List.of() : List.of(id);
            }
        };
    }

    /**
     * 解析文章关联 ID：点赞、收藏、浏览等行为取文章 ID
     */
    private Long readArticleRelatedId(Object target) {
        if (target instanceof Number number) {
            return number.longValue();
        }
        return SyncEventCollector.readLong(target, "articleId");
    }

    /**
     * 解析关注行为的目标用户 ID
     * 关注新增接口入参是 FocusDTO（userId + focusId），取消关注接口入参是两个 RequestParam，
     * 两者都需要取 focusId 作为目标用户，不能取 userId，否则会记录成关注自己
     */
    private Long resolveFocusTarget(ProceedingJoinPoint joinPoint, Object primaryParam) {
        Long focusId = SyncEventCollector.readLong(primaryParam, "focusId");
        if (focusId != null) {
            return focusId;
        }
        return readParameterId(joinPoint, "focusId");
    }

    /**
     * 按方法参数名解析 Long 型参数，AspectJ 依赖只保留在切面内，采集工具保持与 AspectJ 无关
     */
    private Long readParameterId(ProceedingJoinPoint joinPoint, String parameterName) {
        String[] parameterNames = ((MethodSignature) joinPoint.getSignature()).getParameterNames();
        return SyncEventCollector.readByName(parameterNames, joinPoint.getArgs(), parameterName);
    }
}
