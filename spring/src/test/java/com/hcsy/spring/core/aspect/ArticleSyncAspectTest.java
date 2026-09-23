package com.hcsy.spring.core.aspect;

import java.lang.reflect.Method;
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
import com.hcsy.spring.common.utils.RabbitMQUtil;
import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.core.annotation.ArticleSync;
import com.hcsy.spring.entity.dto.ArticleCollectDTO;
import com.hcsy.spring.entity.dto.ArticleLikeDTO;
import com.hcsy.spring.entity.dto.FocusDTO;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyBoolean;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.lenient;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

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
        lenient().when(asyncSyncService.syncAllAsync(any(), any(), anyBoolean(), anyBoolean()))
            .thenReturn(Mono.empty());
        lenient().when(asyncSyncService.syncNeo4jAsync(anyString(), anyString()))
            .thenReturn(Mono.empty());
    }

    @Test
    @DisplayName("业务成功时触发 MQ 与下游同步")
    void triggersSyncOnBusinessSuccess() throws Throwable {
        Mono<?> result = invoke("likeSuccess", "like", new Class<?>[] { ArticleLikeDTO.class },
            new ArticleLikeDTO(21L, 7L));

        StepVerifier.create(result).expectNextCount(1).verifyComplete();

        verify(rabbitMQUtil).sendMessage(eq("article-log-queue"), any());
        verify(asyncSyncService).syncAllAsync(any(), any(), eq(false), eq(false));
        verify(asyncSyncService).syncNeo4jAsync(anyString(), anyString());
    }

    @Test
    @DisplayName("业务失败时不触发任何同步")
    void skipsSyncOnBusinessFailure() throws Throwable {
        Mono<?> result = invoke("likeConflict", "like", new Class<?>[] { ArticleLikeDTO.class },
            new ArticleLikeDTO(21L, 7L));

        StepVerifier.create(result).expectNextCount(1).verifyComplete();

        verify(rabbitMQUtil, never()).sendMessage(anyString(), any());
        verify(asyncSyncService, never()).syncAllAsync(any(), any(), anyBoolean(), anyBoolean());
        verify(asyncSyncService, never()).syncNeo4jAsync(anyString(), anyString());
    }

    @Test
    @DisplayName("文章新增开启 ES 与向量库同步开关")
    void passesSyncSwitchesFromAnnotation() throws Throwable {
        Mono<?> result = invoke("addWithSwitches", "add", new Class<?>[] { ArticleLikeDTO.class },
            new ArticleLikeDTO(21L, 7L));

        StepVerifier.create(result).expectNextCount(1).verifyComplete();

        verify(asyncSyncService).syncAllAsync(any(), any(), eq(true), eq(true));
    }

    @Test
    @DisplayName("点赞按 DTO 属性解析文章 ID 写入消息")
    void resolvesArticleIdFromLikeDto() throws Throwable {
        subscribe("likeSuccess", "like", new Class<?>[] { ArticleLikeDTO.class },
            new ArticleLikeDTO(21L, 7L));

        Map<String, Object> message = captureSentMessage();
        assert message.get("articleId").equals(21L);
    }

    @Test
    @DisplayName("收藏按 DTO 属性解析文章 ID 写入消息")
    void resolvesArticleIdFromCollectDto() throws Throwable {
        subscribe("collectSuccess", "collect", new Class<?>[] { ArticleCollectDTO.class },
            new ArticleCollectDTO(33L, 7L));

        Map<String, Object> message = captureSentMessage();
        assert message.get("articleId").equals(33L);
    }

    @Test
    @DisplayName("关注把双方用户写入 content，articleId 用 -1 占位")
    void recordsBothUsersInContentForFocus() throws Throwable {
        subscribe("focusSuccess", "focus", new Class<?>[] { FocusDTO.class },
            new FocusDTO(7L, 200L));

        Map<String, Object> message = captureSentMessage();
        // 发起者写在顶层 userId
        assert message.get("userId").equals(7L);
        // 关注与文章无关，articleId 传 -1 占位，与 GoZero 搜索日志的约定一致
        assert message.get("articleId").equals(-1L);
        assert !message.containsKey("targetUserId");

        @SuppressWarnings("unchecked")
        Map<String, Object> content = (Map<String, Object>) message.get("content");
        assert content.get("id").equals(200L);
        assert content.get("sourceUserId").equals(7L);
        assert content.get("targetUserId").equals(200L);
    }

    @Test
    @DisplayName("关注不能把发起者当成被关注者")
    void focusDoesNotFallbackToSourceUser() throws Throwable {
        // FocusDTO 同时含 focusId 与 user_id，必须取 focusId
        subscribe("focusSuccess", "focus", new Class<?>[] { FocusDTO.class },
            new FocusDTO(7L, 200L));

        @SuppressWarnings("unchecked")
        Map<String, Object> content = (Map<String, Object>) captureSentMessage().get("content");
        assert !content.get("targetUserId").equals(content.get("sourceUserId"));
        assert content.get("targetUserId").equals(200L);
    }

    @Test
    @DisplayName("批量删除按逗号分隔字符串解析出多个 ID")
    void resolvesBatchDeleteIds() throws Throwable {
        subscribe("deleteBatch", "delete", new Class<?>[] { String.class }, "21,22,23");

        Map<String, Object> message = captureSentMessage();
        assert message.get("articleIds") instanceof java.util.List<?> ids
            && ids.size() == 3;
    }

    @Test
    @DisplayName("单个删除只写入单个文章 ID")
    void resolvesSingleDeleteId() throws Throwable {
        subscribe("deleteSingle", "delete", new Class<?>[] { Long.class }, 21L);

        Map<String, Object> message = captureSentMessage();
        assert message.get("articleId").equals(21L);
        assert !message.containsKey("articleIds");
    }

    /**
     * 订阅切面返回的 Mono，让 doOnSuccess 中的同步真正执行
     */
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
        lenient().when(articleSync.esSync()).thenReturn("addWithSwitches".equals(methodName));
        lenient().when(articleSync.vectorSync()).thenReturn("addWithSwitches".equals(methodName));

        Mono<?> result = (Mono<?>) aspect.handleArticleSync(joinPoint, articleSync);
        // 同步在 doOnSuccess 中订阅，需要带上下文订阅才能执行
        return result.contextWrite(Context.of(
            com.hcsy.spring.common.utils.UserContext.CONTEXT_KEY_USER_ID, 7L,
            com.hcsy.spring.common.utils.UserContext.CONTEXT_KEY_USERNAME, "tester"));
    }

    private Result<?> businessResult(Method method) {
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

        public Mono<Result<Void>> deleteBatch(String ids) {
            return Mono.just(Result.success());
        }

        public Mono<Result<Void>> deleteSingle(Long id) {
            return Mono.just(Result.success());
        }
    }
}
