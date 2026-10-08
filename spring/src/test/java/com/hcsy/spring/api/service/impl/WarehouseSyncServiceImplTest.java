package com.hcsy.spring.api.service.impl;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyInt;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.time.LocalDateTime;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import com.hcsy.spring.api.repository.WarehouseSyncRepository;
import com.hcsy.spring.entity.po.Article;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

@ExtendWith(MockitoExtension.class)
class WarehouseSyncServiceImplTest {

    private static final LocalDateTime UPPER_WATERMARK = LocalDateTime.parse("2026-05-01T00:00:00");
    private static final LocalDateTime UPDATED_AFTER = LocalDateTime.parse("2026-04-01T00:00:00");

    @Mock
    private WarehouseSyncRepository warehouseSyncRepository;

    private WarehouseSyncServiceImpl warehouseSyncService;

    @BeforeEach
    void setUp() {
        warehouseSyncService = new WarehouseSyncServiceImpl(warehouseSyncRepository);
    }

    @Test
    @DisplayName("不支持的数据仓资源直接返回非法参数错误且不查询数据库")
    void rejectsUnsupportedResource() {
        StepVerifier.create(warehouseSyncService.sync("unknown", null, 1, 10))
            .expectErrorMatches(error -> error instanceof IllegalArgumentException
                && error.getMessage().contains("unknown"))
            .verify();

        verify(warehouseSyncRepository, never()).findLatest(any(), anyString());
    }

    @Test
    @DisplayName("资源不存在时返回空页并跳过区间查询")
    void returnsEmptyPageWhenNoData() {
        when(warehouseSyncRepository.findLatest(Article.class, "updateAt")).thenReturn(Mono.empty());

        StepVerifier.create(warehouseSyncService.sync("articles", null, 1, 10))
            .assertNext(page -> {
                assertThat(page.list()).isEmpty();
                assertThat(page.hasMore()).isFalse();
                assertThat(page.upperWatermark()).isNull();
            })
            .verifyComplete();

        verify(warehouseSyncRepository, never()).findUpdated(any(), anyString(), any(), any(), anyInt(),
            anyInt());
    }

    @Test
    @DisplayName("非法页码与超限每页大小被归一化后查询")
    void normalizesPageAndSizeBeforeQuery() {
        when(warehouseSyncRepository.findLatest(Article.class, "updateAt"))
            .thenReturn(Mono.just(article(UPPER_WATERMARK)));
        when(warehouseSyncRepository.findUpdated(Article.class, "updateAt", null, UPPER_WATERMARK, 0, 5001))
            .thenReturn(Flux.empty());

        StepVerifier.create(warehouseSyncService.sync("articles", null, 0, 6000))
            .assertNext(page -> {
                assertThat(page.page()).isEqualTo(1);
                assertThat(page.size()).isEqualTo(5000);
                assertThat(page.hasMore()).isFalse();
            })
            .verifyComplete();
    }

    @Test
    @DisplayName("存在下一条数据时标记 hasMore 并将结果裁剪到请求条数")
    void trimsResultAndFlagsHasMore() {
        when(warehouseSyncRepository.findLatest(Article.class, "updateAt"))
            .thenReturn(Mono.just(article(UPPER_WATERMARK)));
        when(warehouseSyncRepository.findUpdated(Article.class, "updateAt", UPDATED_AFTER, UPPER_WATERMARK, 0, 3))
            .thenReturn(Flux.just(article(UPPER_WATERMARK), article(UPPER_WATERMARK), article(UPPER_WATERMARK)));

        StepVerifier.create(warehouseSyncService.sync("articles", UPDATED_AFTER, 1, 2))
            .assertNext(page -> {
                assertThat(page.hasMore()).isTrue();
                assertThat(page.list()).hasSize(2);
                assertThat(page.upperWatermark()).isEqualTo(UPPER_WATERMARK);
            })
            .verifyComplete();
    }

    private Article article(LocalDateTime updateAt) {
        Article article = new Article();
        article.setId(1L);
        article.setTitle("标题");
        article.setStatus(1);
        article.setViews(3);
        article.setUpdateAt(updateAt);
        return article;
    }
}
