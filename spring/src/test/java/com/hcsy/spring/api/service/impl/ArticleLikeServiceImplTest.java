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

import com.hcsy.spring.api.repository.ArticleLikeRepository;
import com.hcsy.spring.api.service.ArticleService;
import com.hcsy.spring.common.constants.Defaults;
import com.hcsy.spring.entity.assembler.ArticleInteractionAssembler;
import com.hcsy.spring.entity.po.ArticleLike;
import com.hcsy.spring.entity.projection.IdCountRow;
import com.hcsy.spring.entity.vo.ArticleRelationSyncVO;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

@ExtendWith(MockitoExtension.class)
class ArticleLikeServiceImplTest {

    private static final Long ARTICLE_ID = 7L;
    private static final Long USER_ID = 3L;
    private static final LocalDateTime LIKED_TIME = LocalDateTime.parse("2026-02-01T08:30:00");

    @Mock
    private ArticleLikeRepository articleLikeRepository;
    @Mock
    private ArticleInteractionAssembler assembler;
    @Mock
    private TransactionalOperator transactionalOperator;
    @Mock
    private ArticleService articleService;

    private ArticleLikeServiceImpl articleLikeService;

    @BeforeEach
    void setUp() {
        articleLikeService = new ArticleLikeServiceImpl(articleLikeRepository, assembler, transactionalOperator,
            articleService);
    }

    @Test
    @DisplayName("重复点赞返回失败且不写入记录")
    void addLikeRejectsDuplicate() {
        when(articleLikeRepository.existsByArticleIdAndUserId(ARTICLE_ID, USER_ID)).thenReturn(Mono.just(true));
        stubTransactional();

        StepVerifier.create(articleLikeService.addLike(ARTICLE_ID, USER_ID))
            .expectNext(false)
            .verifyComplete();

        verify(articleLikeRepository, never()).save(any(ArticleLike.class));
    }

    @Test
    @DisplayName("首次点赞写入记录并返回成功")
    void addLikePersistsNewRecord() {
        when(articleLikeRepository.existsByArticleIdAndUserId(ARTICLE_ID, USER_ID)).thenReturn(Mono.just(false));
        stubTransactional();
        when(articleLikeRepository.save(any(ArticleLike.class))).thenReturn(Mono.just(new ArticleLike()));

        StepVerifier.create(articleLikeService.addLike(ARTICLE_ID, USER_ID))
            .expectNext(true)
            .verifyComplete();

        ArgumentCaptor<ArticleLike> captor = ArgumentCaptor.forClass(ArticleLike.class);
        verify(articleLikeRepository).save(captor.capture());
        assertThat(captor.getValue().getArticleId()).isEqualTo(ARTICLE_ID);
        assertThat(captor.getValue().getUserId()).isEqualTo(USER_ID);
        assertThat(captor.getValue().getCreatedTime()).isNotNull();
    }

    @Test
    @DisplayName("取消未点赞的记录返回失败且不执行删除")
    void removeLikeRejectsMissingRecord() {
        when(articleLikeRepository.existsByArticleIdAndUserId(ARTICLE_ID, USER_ID)).thenReturn(Mono.just(false));
        stubTransactional();

        StepVerifier.create(articleLikeService.removeLike(ARTICLE_ID, USER_ID))
            .expectNext(false)
            .verifyComplete();

        verify(articleLikeRepository, never()).deleteByArticleIdAndUserId(any(), any());
    }

    @Test
    @DisplayName("取消已点赞的记录返回成功并执行删除")
    void removeLikeDeletesExistingRecord() {
        when(articleLikeRepository.existsByArticleIdAndUserId(ARTICLE_ID, USER_ID)).thenReturn(Mono.just(true));
        when(articleLikeRepository.deleteByArticleIdAndUserId(ARTICLE_ID, USER_ID)).thenReturn(Mono.empty());
        stubTransactional();

        StepVerifier.create(articleLikeService.removeLike(ARTICLE_ID, USER_ID))
            .expectNext(true)
            .verifyComplete();

        verify(articleLikeRepository).deleteByArticleIdAndUserId(ARTICLE_ID, USER_ID);
    }

    @Test
    @DisplayName("批量统计点赞数时空入参直接返回空结果")
    void getLikeCountsSkipsEmptyInput() {
        StepVerifier.create(articleLikeService.getLikeCountsByArticleIds(List.of()))
            .assertNext(counts -> assertThat(counts.getCounts()).isEmpty())
            .verifyComplete();

        verify(articleLikeRepository, never()).countGroupByArticleIdIn(any());
    }

    @Test
    @DisplayName("批量统计点赞数时把投影转换为 ID 计数项")
    void getLikeCountsMapsRows() {
        IdCountRow row = mock(IdCountRow.class);
        when(row.getId()).thenReturn(ARTICLE_ID);
        when(row.getCount()).thenReturn(4L);
        when(articleLikeRepository.countGroupByArticleIdIn(List.of(ARTICLE_ID))).thenReturn(Flux.just(row));

        StepVerifier.create(articleLikeService.getLikeCountsByArticleIds(List.of(ARTICLE_ID)))
            .assertNext(counts -> {
                assertThat(counts.getCounts()).hasSize(1);
                assertThat(counts.getCounts().get(0).getCount()).isEqualTo(4L);
            })
            .verifyComplete();
    }

    @Test
    @DisplayName("没有文章时平均点赞数返回零")
    void getAverageLikesReturnsZeroWhenNoArticle() {
        when(articleService.getTotalArticles()).thenReturn(Mono.just(0L));
        when(articleLikeRepository.count()).thenReturn(Mono.just(5L));

        StepVerifier.create(articleLikeService.getAverageLikes()).expectNext(0.0).verifyComplete();
    }

    @Test
    @DisplayName("平均点赞数按两位小数四舍五入")
    void getAverageLikesRoundsToTwoDecimals() {
        when(articleService.getTotalArticles()).thenReturn(Mono.just(4L));
        when(articleLikeRepository.count()).thenReturn(Mono.just(6L));

        StepVerifier.create(articleLikeService.getAverageLikes()).expectNext(1.5).verifyComplete();
    }

    @Test
    @DisplayName("全量同步点赞时按上限抓取最近记录并转换关系视图")
    void getNeo4jSyncLikesUsesLimitedLatestQuery() {
        ArticleLike like = new ArticleLike();
        like.setUserId(USER_ID);
        like.setArticleId(ARTICLE_ID);
        like.setCreatedTime(LIKED_TIME);
        when(articleLikeRepository.findLatestForSync(Defaults.NEO4J_SYNC_LIMIT)).thenReturn(Flux.just(like));

        StepVerifier.create(articleLikeService.getNeo4jSyncLikes(null))
            .assertNext(list -> {
                assertThat(list).hasSize(1);
                ArticleRelationSyncVO vo = list.get(0);
                assertThat(vo.getUserId()).isEqualTo(USER_ID);
                assertThat(vo.getArticleId()).isEqualTo(ARTICLE_ID);
                assertThat(vo.getCreatedTime()).isEqualTo(LIKED_TIME);
            })
            .verifyComplete();
    }

    @Test
    @DisplayName("增量同步点赞时按时间戳过滤")
    void getNeo4jSyncLikesUsesAfterWhenProvided() {
        when(articleLikeRepository.findLatestAfterForSync(LIKED_TIME, Defaults.NEO4J_SYNC_LIMIT))
            .thenReturn(Flux.empty());

        StepVerifier.create(articleLikeService.getNeo4jSyncLikes("2026-02-01T08:30:00"))
            .assertNext(list -> assertThat(list).isEmpty())
            .verifyComplete();
    }

    private void stubTransactional() {
        when(transactionalOperator.transactional(any(Mono.class)))
            .thenAnswer(invocation -> invocation.getArgument(0));
    }
}
