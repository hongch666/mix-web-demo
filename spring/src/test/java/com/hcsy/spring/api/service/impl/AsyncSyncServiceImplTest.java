package com.hcsy.spring.api.service.impl;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyList;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.util.List;
import java.util.Set;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.entity.event.ChangeEvent;
import com.hcsy.spring.infra.client.FastAPIClient;
import com.hcsy.spring.infra.client.GoZeroClient;

import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

@ExtendWith(MockitoExtension.class)
class AsyncSyncServiceImplTest {

    private static final Long USER_ID = 1L;
    private static final String USERNAME = "alice";

    @Mock
    private GoZeroClient goZeroClient;
    @Mock
    private FastAPIClient fastAPIClient;
    @Mock
    private SimpleLogger logger;

    private AsyncSyncServiceImpl asyncSyncService;

    @BeforeEach
    void setUp() {
        asyncSyncService = new AsyncSyncServiceImpl(goZeroClient, fastAPIClient, logger);
    }

    @Test
    @DisplayName("文章变更同时开启 ES 与向量同步时触发三个下游任务")
    void syncArticleTriggersAllRequestedTargets() {
        ChangeEvent event = changeEvent();
        when(goZeroClient.syncES(event)).thenReturn(okResult());
        when(fastAPIClient.syncVector(event)).thenReturn(okResult());
        when(fastAPIClient.syncWarehouse(Set.of("articles"))).thenReturn(okResult());

        StepVerifier.create(asyncSyncService.syncArticleAsync(USER_ID, USERNAME, true, true, event))
            .verifyComplete();

        verify(goZeroClient).syncES(event);
        verify(fastAPIClient).syncVector(event);
        verify(fastAPIClient).syncWarehouse(Set.of("articles"));
    }

    @Test
    @DisplayName("文章变更关闭 ES 与向量同步时只刷新数仓")
    void syncArticleOnlyRefreshesWarehouseWhenTargetsDisabled() {
        ChangeEvent event = changeEvent();
        when(fastAPIClient.syncWarehouse(Set.of("articles"))).thenReturn(okResult());

        StepVerifier.create(asyncSyncService.syncArticleAsync(USER_ID, USERNAME, false, false, event))
            .verifyComplete();

        verify(goZeroClient, never()).syncES(any());
        verify(fastAPIClient, never()).syncVector(any());
        verify(fastAPIClient).syncWarehouse(Set.of("articles"));
    }

    @Test
    @DisplayName("下游返回非成功错误码时同步链路报错")
    void syncArticleFailsWhenDownstreamReturnsErrorCode() {
        ChangeEvent event = changeEvent();
        when(goZeroClient.syncES(event)).thenReturn(failedResult("es boom"));
        when(fastAPIClient.syncWarehouse(Set.of("articles"))).thenReturn(okResult());

        StepVerifier.create(asyncSyncService.syncArticleAsync(USER_ID, USERNAME, true, false, event))
            .expectErrorMatches(error -> error instanceof IllegalStateException
                && "es boom".equals(error.getMessage()))
            .verify();
    }

    @Test
    @DisplayName("数仓同步按传入资源集合触发下游")
    void syncWarehouseForwardsResourceSet() {
        Set<String> resources = Set.of("likes", "focus");
        when(fastAPIClient.syncWarehouse(resources)).thenReturn(okResult());

        StepVerifier.create(asyncSyncService.syncWarehouseAsync(USER_ID, USERNAME, resources)).verifyComplete();

        verify(fastAPIClient).syncWarehouse(resources);
    }

    @Test
    @DisplayName("图谱同步提交成功后正常完成")
    void syncNeo4jCompletesOnSuccess() {
        ChangeEvent event = changeEvent();
        when(fastAPIClient.syncNeo4j(List.of(event))).thenReturn(okResult());

        StepVerifier.create(asyncSyncService.syncNeo4jAsync("createArticle", "新增文章", event)).verifyComplete();

        verify(fastAPIClient).syncNeo4j(List.of(event));
    }

    @Test
    @DisplayName("图谱同步提交失败时降级完成而不是向外抛错")
    void syncNeo4jDegradesOnFailure() {
        when(fastAPIClient.syncNeo4j(anyList()))
            .thenReturn(Mono.error(new IllegalStateException("neo4j down")));

        StepVerifier.create(asyncSyncService.syncNeo4jAsync("createArticle", "新增文章", changeEvent()))
            .verifyComplete();
    }

    private ChangeEvent changeEvent() {
        return ChangeEvent.builder().resource("articles").changeType("create").ids(List.of(1L)).build();
    }

    private Mono<Result<?>> okResult() {
        return Mono.just(Result.success());
    }

    private Mono<Result<?>> failedResult(String message) {
        return Mono.just(Result.error(message));
    }
}
