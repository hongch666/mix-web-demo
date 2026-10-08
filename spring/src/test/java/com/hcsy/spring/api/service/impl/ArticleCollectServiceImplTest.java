package com.hcsy.spring.api.service.impl;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.time.LocalDateTime;
import java.util.List;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.transaction.reactive.TransactionalOperator;

import com.hcsy.spring.api.repository.ArticleCollectRepository;
import com.hcsy.spring.api.service.ArticleService;
import com.hcsy.spring.common.constants.Defaults;
import com.hcsy.spring.entity.assembler.ArticleInteractionAssembler;
import com.hcsy.spring.entity.po.ArticleCollect;
import com.hcsy.spring.entity.projection.IdCountRow;
import com.hcsy.spring.entity.vo.ArticleRelationSyncVO;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

@ExtendWith(MockitoExtension.class)
class ArticleCollectServiceImplTest {

    private static final Long ARTICLE_ID = 7L;
    private static final Long USER_ID = 3L;
    private static final LocalDateTime COLLECTED_TIME = LocalDateTime.parse("2026-02-02T09:00:00");

    @Mock
    private ArticleCollectRepository articleCollectRepository;
    @Mock
    private ArticleInteractionAssembler assembler;
    @Mock
    private TransactionalOperator transactionalOperator;
    @Mock
    private ArticleService articleService;

    private ArticleCollectServiceImpl articleCollectService;

    @BeforeEach
    void setUp() {
        articleCollectService = new ArticleCollectServiceImpl(articleCollectRepository, assembler,
            transactionalOperator, articleService);
    }

    @Test
    @DisplayName("重复收藏返回失败且不写入记录")
    void addCollectRejectsDuplicate() {
        when(articleCollectRepository.existsByArticleIdAndUserId(ARTICLE_ID, USER_ID)).thenReturn(Mono.just(true));
        stubTransactional();

        StepVerifier.create(articleCollectService.addCollect(ARTICLE_ID, USER_ID))
            .expectNext(false)
            .verifyComplete();

        verify(articleCollectRepository, never()).save(any(ArticleCollect.class));
    }

    @Test
    @DisplayName("首次收藏写入记录并返回成功")
    void addCollectPersistsNewRecord() {
        when(articleCollectRepository.existsByArticleIdAndUserId(ARTICLE_ID, USER_ID)).thenReturn(Mono.just(false));
        stubTransactional();
        when(articleCollectRepository.save(any(ArticleCollect.class))).thenReturn(Mono.just(new ArticleCollect()));

        StepVerifier.create(articleCollectService.addCollect(ARTICLE_ID, USER_ID))
            .expectNext(true)
            .verifyComplete();

        ArgumentCaptor<ArticleCollect> captor = ArgumentCaptor.forClass(ArticleCollect.class);
        verify(articleCollectRepository).save(captor.capture());
        assertThat(captor.getValue().getArticleId()).isEqualTo(ARTICLE_ID);
        assertThat(captor.getValue().getUserId()).isEqualTo(USER_ID);
        assertThat(captor.getValue().getCreatedTime()).isNotNull();
    }

    @Test
    @DisplayName("取消未收藏的记录返回失败且不执行删除")
    void removeCollectRejectsMissingRecord() {
        when(articleCollectRepository.existsByArticleIdAndUserId(ARTICLE_ID, USER_ID)).thenReturn(Mono.just(false));
        stubTransactional();

        StepVerifier.create(articleCollectService.removeCollect(ARTICLE_ID, USER_ID))
            .expectNext(false)
            .verifyComplete();

        verify(articleCollectRepository, never()).deleteByArticleIdAndUserId(any(), any());
    }

    @Test
    @DisplayName("取消已收藏的记录返回成功并执行删除")
    void removeCollectDeletesExistingRecord() {
        when(articleCollectRepository.existsByArticleIdAndUserId(ARTICLE_ID, USER_ID)).thenReturn(Mono.just(true));
        when(articleCollectRepository.deleteByArticleIdAndUserId(ARTICLE_ID, USER_ID)).thenReturn(Mono.empty());
        stubTransactional();

        StepVerifier.create(articleCollectService.removeCollect(ARTICLE_ID, USER_ID))
            .expectNext(true)
            .verifyComplete();

        verify(articleCollectRepository).deleteByArticleIdAndUserId(ARTICLE_ID, USER_ID);
    }

    @Test
    @DisplayName("批量统计收藏数时空入参直接返回空结果")
    void getCollectCountsSkipsEmptyInput() {
        StepVerifier.create(articleCollectService.getCollectCountsByArticleIds(List.of()))
            .assertNext(counts -> assertThat(counts.getCounts()).isEmpty())
            .verifyComplete();

        verify(articleCollectRepository, never()).countGroupByArticleIdIn(any());
    }

    @Test
    @DisplayName("批量统计收藏数时把投影转换为 ID 计数项")
    void getCollectCountsMapsRows() {
        IdCountRow row = mock(IdCountRow.class);
        when(row.getId()).thenReturn(ARTICLE_ID);
        when(row.getCount()).thenReturn(2L);
        when(articleCollectRepository.countGroupByArticleIdIn(List.of(ARTICLE_ID))).thenReturn(Flux.just(row));

        StepVerifier.create(articleCollectService.getCollectCountsByArticleIds(List.of(ARTICLE_ID)))
            .assertNext(counts -> {
                assertThat(counts.getCounts()).hasSize(1);
                assertThat(counts.getCounts().get(0).getId()).isEqualTo(ARTICLE_ID);
                assertThat(counts.getCounts().get(0).getCount()).isEqualTo(2L);
            })
            .verifyComplete();
    }

    @Test
    @DisplayName("没有文章时平均收藏数返回零")
    void getAverageCollectsReturnsZeroWhenNoArticle() {
        when(articleService.getTotalArticles()).thenReturn(Mono.just(0L));
        when(articleCollectRepository.count()).thenReturn(Mono.just(5L));

        StepVerifier.create(articleCollectService.getAverageCollects()).expectNext(0.0).verifyComplete();
    }

    @Test
    @DisplayName("平均收藏数按两位小数四舍五入")
    void getAverageCollectsRoundsToTwoDecimals() {
        when(articleService.getTotalArticles()).thenReturn(Mono.just(3L));
        when(articleCollectRepository.count()).thenReturn(Mono.just(1L));

        StepVerifier.create(articleCollectService.getAverageCollects()).expectNext(0.33).verifyComplete();
    }

    @Test
    @DisplayName("全量同步收藏时按上限抓取最近记录并转换关系视图")
    void getNeo4jSyncCollectsUsesLimitedLatestQuery() {
        ArticleCollect collect = new ArticleCollect();
        collect.setUserId(USER_ID);
        collect.setArticleId(ARTICLE_ID);
        collect.setCreatedTime(COLLECTED_TIME);
        when(articleCollectRepository.findLatestForSync(Defaults.NEO4J_SYNC_LIMIT)).thenReturn(Flux.just(collect));

        StepVerifier.create(articleCollectService.getNeo4jSyncCollects("  "))
            .assertNext(list -> {
                assertThat(list).hasSize(1);
                ArticleRelationSyncVO vo = list.get(0);
                assertThat(vo.getUserId()).isEqualTo(USER_ID);
                assertThat(vo.getArticleId()).isEqualTo(ARTICLE_ID);
                assertThat(vo.getCreatedTime()).isEqualTo(COLLECTED_TIME);
            })
            .verifyComplete();
    }

    @Test
    @DisplayName("增量同步收藏时按时间戳过滤")
    void getNeo4jSyncCollectsUsesAfterWhenProvided() {
        when(articleCollectRepository.findLatestAfterForSync(COLLECTED_TIME, Defaults.NEO4J_SYNC_LIMIT))
            .thenReturn(Flux.empty());

        StepVerifier.create(articleCollectService.getNeo4jSyncCollects("2026-02-02T09:00:00"))
            .assertNext(list -> assertThat(list).isEmpty())
            .verifyComplete();
    }

    private void stubTransactional() {
        when(transactionalOperator.transactional(any(Mono.class)))
            .thenAnswer(invocation -> invocation.getArgument(0));
    }
}
