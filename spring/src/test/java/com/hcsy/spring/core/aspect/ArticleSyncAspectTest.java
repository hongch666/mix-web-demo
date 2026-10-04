package com.hcsy.spring.core.aspect;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyBoolean;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.lenient;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.lang.reflect.Method;
import java.util.List;
import java.util.Map;

import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.reflect.MethodSignature;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import com.hcsy.spring.api.service.AsyncSyncService;
import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.constants.SyncChangeType;
import com.hcsy.spring.common.constants.SyncResource;
import com.hcsy.spring.common.utils.RabbitMQUtil;
import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.core.annotation.ArticleSync;
import com.hcsy.spring.entity.dto.ArticleCollectDTO;
import com.hcsy.spring.entity.dto.ArticleCreateDTO;
import com.hcsy.spring.entity.dto.ArticleLikeDTO;
import com.hcsy.spring.entity.dto.FocusDTO;
import com.hcsy.spring.entity.event.ChangeEvent;

import com.fasterxml.jackson.databind.ObjectMapper;
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;
import reactor.util.context.Context;

@ExtendWith(MockitoExtension.class)
class ArticleSyncAspectTest {

    @Mock
    private RabbitMQUtil rabbitMQUtil;
    @Mock
    private ObjectMapper objectMapper;
    @Mock
    private SimpleLogger logger;
    @Mock
    private AsyncSyncService asyncSyncService;

    private ArticleSyncAspect aspect;

    @BeforeEach
    void setUp() throws Exception {
        aspect = new ArticleSyncAspect(rabbitMQUtil, objectMapper, logger, asyncSyncService);
        lenient().when(objectMapper.writeValueAsString(any())).thenReturn("{}");
        lenient().when(rabbitMQUtil.sendMessage(anyString(), any())).thenReturn(Mono.empty());
        lenient().when(asyncSyncService.syncArticleAsync(any(), any(), anyBoolean(), anyBoolean(), any()))
            .thenReturn(Mono.empty());
        lenient().when(asyncSyncService.syncNeo4jAsync(anyString(), anyString(), any()))
            .thenReturn(Mono.empty());
    }

    @Test
    @DisplayName("业务成功时触发 MQ 与下游精确同步")
    void triggersSyncOnBusinessSuccess() throws Throwable {
        Mono<?> result = invoke("likeSuccess", "like", new Class<?>[] { ArticleLikeDTO.class },
            new ArticleLikeDTO(21L, 7L));

        StepVerifier.create(result).expectNextCount(1).verifyComplete();

        verify(rabbitMQUtil).sendMessage(eq("article-log-queue"), any());
        verify(asyncSyncService).syncArticleAsync(any(), any(), eq(false), eq(false), any());
        verify(asyncSyncService).syncNeo4jAsync(anyString(), anyString(), any());
    }

    @Test
    @DisplayName("业务失败时不触发任何同步")
    void skipsSyncOnBusinessFailure() throws Throwable {
        Mono<?> result = invoke("likeConflict", "like", new Class<?>[] { ArticleLikeDTO.class },
            new ArticleLikeDTO(21L, 7L));

        StepVerifier.create(result).expectNextCount(1).verifyComplete();

        verify(rabbitMQUtil, never()).sendMessage(anyString(), any());
        verify(asyncSyncService, never()).syncArticleAsync(any(), any(), anyBoolean(), anyBoolean(), any());
        verify(asyncSyncService, never()).syncNeo4jAsync(anyString(), anyString(), any());
    }

    @Test
    @DisplayName("文章新增开启 ES 与向量库同步开关")
    void passesSyncSwitchesFromAnnotation() throws Throwable {
        Mono<?> result = invoke("addWithSwitches", "add", new Class<?>[] { ArticleLikeDTO.class },
            new ArticleLikeDTO(21L, 7L));

        StepVerifier.create(result).expectNextCount(1).verifyComplete();

        verify(asyncSyncService).syncArticleAsync(any(), any(), eq(true), eq(true), any());
    }

    @Test
    @DisplayName("点赞按 DTO 属性解析文章 ID 写入消息")
    void resolvesArticleIdFromLikeDto() throws Throwable {
        subscribe("likeSuccess", "like", new Class<?>[] { ArticleLikeDTO.class },
            new ArticleLikeDTO(21L, 7L));

        Map<String, Object> message = captureSentMessage();
        assertEquals(21L, message.get("articleId"));
    }

    @Test
    @DisplayName("收藏按 DTO 属性解析文章 ID 写入消息")
    void resolvesArticleIdFromCollectDto() throws Throwable {
        subscribe("collectSuccess", "collect", new Class<?>[] { ArticleCollectDTO.class },
            new ArticleCollectDTO(33L, 7L));

        Map<String, Object> message = captureSentMessage();
        assertEquals(33L, message.get("articleId"));
    }

    @Test
    @DisplayName("关注把双方用户写入 content，articleId 用 -1 占位")
    void recordsBothUsersInContentForFocus() throws Throwable {
        subscribe("focusSuccess", "focus", new Class<?>[] { FocusDTO.class },
            new FocusDTO(7L, 200L));

        Map<String, Object> message = captureSentMessage();
        assertEquals(7L, message.get("userId"));
        assertEquals(-1L, message.get("articleId"));
        assertFalse(message.containsKey("targetUserId"));

        @SuppressWarnings("unchecked")
        Map<String, Object> content = (Map<String, Object>) message.get("content");
        assertEquals(200L, content.get("id"));
        assertEquals(7L, content.get("sourceUserId"));
        assertEquals(200L, content.get("targetUserId"));
    }

    @Test
    @DisplayName("关注不能把发起者当成被关注者")
    void focusDoesNotFallbackToSourceUser() throws Throwable {
        subscribe("focusSuccess", "focus", new Class<?>[] { FocusDTO.class },
            new FocusDTO(7L, 200L));

        @SuppressWarnings("unchecked")
        Map<String, Object> content = (Map<String, Object>) captureSentMessage().get("content");
        assertFalse(content.get("targetUserId").equals(content.get("sourceUserId")));
        assertEquals(200L, content.get("targetUserId"));
    }

    @Test
    @DisplayName("批量删除按逗号分隔字符串解析出多个 ID")
    void resolvesBatchDeleteIds() throws Throwable {
        subscribe("deleteBatch", "delete", new Class<?>[] { String.class }, "21,22,23");

        Map<String, Object> message = captureSentMessage();
        assertEquals(3, ((List<?>) message.get("articleIds")).size());
    }

    @Test
    @DisplayName("单个删除只写入单个文章 ID")
    void resolvesSingleDeleteId() throws Throwable {
        subscribe("deleteSingle", "delete", new Class<?>[] { Long.class }, 21L);

        Map<String, Object> message = captureSentMessage();
        assertEquals(21L, message.get("articleId"));
        assertFalse(message.containsKey("articleIds"));
    }

    @Test
    @DisplayName("删除精确下发受影响主键与变更类型")
    void dispatchesExactDeleteEvent() throws Throwable {
        subscribe("deleteBatch", "delete", new Class<?>[] { String.class }, "21,22,23");

        ChangeEvent event = captureSentEvent();
        assertEquals(SyncChangeType.DELETE.value(), event.getChangeType());
        assertEquals(SyncResource.ARTICLES, event.getResource());
        assertEquals(List.of(21L, 22L, 23L), event.getIds());
    }

    @Test
    @DisplayName("新增文章从业务返回值解析新主键并精确下发")
    void dispatchesInsertEventFromResultId() throws Throwable {
        subscribe("addArticle", "add", new Class<?>[] { ArticleCreateDTO.class }, new ArticleCreateDTO());

        ChangeEvent event = captureSentEvent();
        assertEquals(SyncChangeType.INSERT.value(), event.getChangeType());
        assertEquals(List.of(100L), event.getIds());
    }

    @Test
    @DisplayName("点赞事件携带触发用户与目标文章主键")
    void dispatchesLikeEventWithTriggerUser() throws Throwable {
        subscribe("likeSuccess", "like", new Class<?>[] { ArticleLikeDTO.class },
            new ArticleLikeDTO(21L, 7L));

        ChangeEvent event = captureSentEvent();
        assertEquals(21L, event.getIds().get(0));
        assertEquals(7L, event.getTriggerUserId());
    }

    private void subscribe(String methodName, String action, Class<?>[] parameterTypes,
        Object... arguments) throws Throwable {
        StepVerifier.create(invoke(methodName, action, parameterTypes, arguments))
            .expectNextCount(1)
            .verifyComplete();
    }

    @SuppressWarnings("unchecked")
    private Map<String, Object> captureSentMessage() throws Throwable {
        ArgumentCaptor<Map<String, Object>> captor = ArgumentCaptor.forClass(Map.class);
        verify(rabbitMQUtil).sendMessage(eq("article-log-queue"), captor.capture());
        return captor.getValue();
    }

    private ChangeEvent captureSentEvent() {
        ArgumentCaptor<ChangeEvent> captor = ArgumentCaptor.forClass(ChangeEvent.class);
        verify(asyncSyncService).syncArticleAsync(any(), any(), anyBoolean(), anyBoolean(), captor.capture());
        return captor.getValue();
    }

    private Mono<?> invoke(String methodName, String action, Class<?>[] parameterTypes,
        Object... arguments) throws Throwable {
        Method method = Fixture.class.getDeclaredMethod(methodName, parameterTypes);
        ProceedingJoinPoint joinPoint = mock(ProceedingJoinPoint.class);
        MethodSignature signature = mock(MethodSignature.class);
        ArticleSync articleSync = mock(ArticleSync.class);

        when(joinPoint.proceed()).thenReturn(Mono.just(businessResult(method)));
        lenient().when(joinPoint.getSignature()).thenReturn(signature);
        lenient().when(joinPoint.getArgs()).thenReturn(arguments);
        lenient().when(signature.toShortString()).thenReturn("fixture." + methodName);
        lenient().when(articleSync.action()).thenReturn(action);
        lenient().when(articleSync.description()).thenReturn("测试描述");
        lenient().when(articleSync.resource()).thenReturn(SyncResource.ARTICLES);
        lenient().when(articleSync.esSync()).thenReturn("addWithSwitches".equals(methodName));
        lenient().when(articleSync.vectorSync()).thenReturn("addWithSwitches".equals(methodName));

        Mono<?> result = (Mono<?>) aspect.handleArticleSync(joinPoint, articleSync);
        return result.contextWrite(Context.of(
            com.hcsy.spring.common.utils.UserContext.CONTEXT_KEY_USER_ID, 7L,
            com.hcsy.spring.common.utils.UserContext.CONTEXT_KEY_USERNAME, "tester"));
    }

    private Result<?> businessResult(Method method) {
        if (method.getName().startsWith("add")) {
            return Result.success(100L);
        }
        boolean success = !method.getName().contains("Conflict");
        return success
            ? Result.success()
            : Result.error(HttpCode.CONFLICT, "冲突");
    }

    /**
     * 被测切面要求的控制器方法签名夹具
     */
    static class Fixture {
        public Mono<Result<Void>> likeSuccess(ArticleLikeDTO dto) {
            return Mono.just(Result.success());
        }

        public Mono<Result<Void>> likeConflict(ArticleLikeDTO dto) {
            return Mono.just(Result.error(HttpCode.CONFLICT, "重复点赞"));
        }

        public Mono<Result<Void>> collectSuccess(ArticleCollectDTO dto) {
            return Mono.just(Result.success());
        }

        public Mono<Result<Void>> focusSuccess(FocusDTO dto) {
            return Mono.just(Result.success());
        }

        public Mono<Result<Void>> addWithSwitches(ArticleLikeDTO dto) {
            return Mono.just(Result.success());
        }

        public Mono<Result<Long>> addArticle(ArticleCreateDTO dto) {
            return Mono.just(Result.success(100L));
        }

        public Mono<Result<Void>> deleteBatch(String ids) {
            return Mono.just(Result.success());
        }

        public Mono<Result<Void>> deleteSingle(Long id) {
            return Mono.just(Result.success());
        }
    }
}
