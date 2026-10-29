package com.hcsy.spring.application.service.impl;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.doReturn;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;

import java.time.LocalDateTime;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentMatchers;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.r2dbc.core.R2dbcEntityTemplate;
import org.springframework.data.relational.core.query.Query;

import com.hcsy.spring.entity.po.Article;

import reactor.core.publisher.Flux;
import reactor.test.StepVerifier;

@ExtendWith(MockitoExtension.class)
class WarehouseSyncServiceImplTest {

    private static final LocalDateTime UPPER_WATERMARK = LocalDateTime.parse("2026-05-01T00:00:00");
    private static final LocalDateTime UPDATED_AFTER = LocalDateTime.parse("2026-04-01T00:00:00");

    @Mock
    private R2dbcEntityTemplate entityTemplate;

    private WarehouseSyncServiceImpl warehouseSyncService;

    @BeforeEach
    void setUp() {
        warehouseSyncService = new WarehouseSyncServiceImpl(entityTemplate);
    }

    @Test
    @DisplayName("不支持的数据仓资源直接返回非法参数错误且不查询数据库")
    void rejectsUnsupportedResource() {
        StepVerifier.create(warehouseSyncService.sync("unknown", null, 1, 10))
            .expectErrorMatches(error -> error instanceof IllegalArgumentException
                && error.getMessage().contains("unknown"))
            .verify();

        verify(entityTemplate, never()).select(any(Query.class), ArgumentMatchers.<Class<Article>>any());
    }

    @Test
    @DisplayName("资源不存在时返回空页并跳过区间查询")
    void returnsEmptyPageWhenNoData() {
        stubSelect(Flux.empty());

        StepVerifier.create(warehouseSyncService.sync("articles", null, 1, 10))
            .assertNext(page -> {
                assertThat(page.list()).isEmpty();
                assertThat(page.hasMore()).isFalse();
                assertThat(page.upperWatermark()).isNull();
            })
            .verifyComplete();

        verify(entityTemplate, times(1)).select(any(Query.class), ArgumentMatchers.<Class<Article>>any());
    }

    @Test
    @DisplayName("非法页码与超限每页大小被归一化后查询")
    void normalizesPageAndSizeBeforeQuery() {
        stubSelect(Flux.just(article(UPPER_WATERMARK)), Flux.empty());

        StepVerifier.create(warehouseSyncService.sync("articles", null, 0, 6000))
            .assertNext(page -> {
                assertThat(page.page()).isEqualTo(1);
                assertThat(page.size()).isEqualTo(5000);
                assertThat(page.hasMore()).isFalse();
            })
            .verifyComplete();

        verify(entityTemplate, times(2)).select(any(Query.class), ArgumentMatchers.<Class<Article>>any());
    }

    @Test
    @DisplayName("存在下一条数据时标记 hasMore 并将结果裁剪到请求条数")
    void trimsResultAndFlagsHasMore() {
        stubSelect(Flux.just(article(UPPER_WATERMARK)),
            Flux.just(article(UPPER_WATERMARK), article(UPPER_WATERMARK), article(UPPER_WATERMARK)));

        StepVerifier.create(warehouseSyncService.sync("articles", UPDATED_AFTER, 1, 2))
            .assertNext(page -> {
                assertThat(page.hasMore()).isTrue();
                assertThat(page.list()).hasSize(2);
                assertThat(page.upperWatermark()).isEqualTo(UPPER_WATERMARK);
            })
            .verifyComplete();
    }

    /**
     * 按调用顺序给定 select 的返回：服务先查水位线上界，再查区间增量数据
     */
    @SafeVarargs
    private final void stubSelect(Flux<Article> first, Flux<Article>... rest) {
        doReturn(first, (Object[]) rest).when(entityTemplate)
            .select(any(Query.class), ArgumentMatchers.<Class<Article>>any());
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
