package com.hcsy.spring.application.service.impl;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.util.List;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import com.hcsy.spring.entity.assembler.CommentScoreAssembler;
import com.hcsy.spring.entity.vo.ArticleCommentScoresVO;
import com.hcsy.spring.entity.vo.IdCountVO;
import com.hcsy.spring.infra.repository.ArticleCollectRepository;
import com.hcsy.spring.infra.repository.ArticleLikeRepository;
import com.hcsy.spring.infra.repository.ArticleRepository;
import com.hcsy.spring.infra.repository.FocusRepository;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

@ExtendWith(MockitoExtension.class)
class ArticleStatsServiceImplTest {

    private static final Long ARTICLE_ID = 8L;
    private static final Long AUTHOR_ID = 5L;

    @Mock
    private ArticleRepository articleRepository;
    @Mock
    private ArticleLikeRepository articleLikeRepository;
    @Mock
    private ArticleCollectRepository articleCollectRepository;
    @Mock
    private FocusRepository focusRepository;
    @Mock
    private CommentScoreAssembler commentScoreAssembler;

    private ArticleStatsServiceImpl articleStatsService;

    @BeforeEach
    void setUp() {
        articleStatsService = new ArticleStatsServiceImpl(articleRepository, articleLikeRepository,
            articleCollectRepository, focusRepository, commentScoreAssembler);
    }

    @Test
    @DisplayName("文章ID为空时返回五项空列表且不访问仓储")
    void getStatsBatchReturnsEmptyWithoutArticleIds() {
        StepVerifier.create(articleStatsService.getStatsBatch(List.of(), List.of(AUTHOR_ID)))
            .assertNext(stats -> {
                assertThat(stats.getViews()).isEmpty();
                assertThat(stats.getLikes()).isEmpty();
                assertThat(stats.getCollects()).isEmpty();
                assertThat(stats.getFollows()).isEmpty();
                assertThat(stats.getCommentScores()).isEmpty();
            })
            .verifyComplete();

        verify(articleRepository, never()).countViewsByIdIn(any());
        verify(commentScoreAssembler, never()).toScoresByArticleIds(any());
    }

    @Test
    @DisplayName("并行聚合并合并五项统计结果")
    void getStatsBatchAggregatesAllSignals() {
        when(articleRepository.countViewsByIdIn(List.of(ARTICLE_ID)))
            .thenReturn(Flux.just(new IdCountVO(ARTICLE_ID, 120L)));
        when(articleLikeRepository.countGroupByArticleIdIn(List.of(ARTICLE_ID)))
            .thenReturn(Flux.just(new IdCountVO(ARTICLE_ID, 4L)));
        when(articleCollectRepository.countGroupByArticleIdIn(List.of(ARTICLE_ID)))
            .thenReturn(Flux.just(new IdCountVO(ARTICLE_ID, 2L)));
        when(focusRepository.countGroupByFocusIdIn(List.of(AUTHOR_ID)))
            .thenReturn(Flux.just(new IdCountVO(AUTHOR_ID, 9L)));
        when(commentScoreAssembler.toScoresByArticleIds(List.of(ARTICLE_ID)))
            .thenReturn(Mono.just(List.of(new ArticleCommentScoresVO(ARTICLE_ID, null))));

        StepVerifier.create(articleStatsService.getStatsBatch(List.of(ARTICLE_ID), List.of(AUTHOR_ID)))
            .assertNext(stats -> {
                assertThat(stats.getViews()).hasSize(1);
                assertThat(stats.getViews().get(0).getCount()).isEqualTo(120L);
                assertThat(stats.getLikes().get(0).getCount()).isEqualTo(4L);
                assertThat(stats.getCollects().get(0).getCount()).isEqualTo(2L);
                assertThat(stats.getFollows().get(0).getId()).isEqualTo(AUTHOR_ID);
                assertThat(stats.getCommentScores()).hasSize(1);
            })
            .verifyComplete();
    }

    @Test
    @DisplayName("作者ID为空时粉丝数为空且不访问关注仓储")
    void getStatsBatchSkipsFollowsWithoutAuthorIds() {
        when(articleRepository.countViewsByIdIn(List.of(ARTICLE_ID))).thenReturn(Flux.empty());
        when(articleLikeRepository.countGroupByArticleIdIn(List.of(ARTICLE_ID))).thenReturn(Flux.empty());
        when(articleCollectRepository.countGroupByArticleIdIn(List.of(ARTICLE_ID))).thenReturn(Flux.empty());
        when(commentScoreAssembler.toScoresByArticleIds(List.of(ARTICLE_ID))).thenReturn(Mono.just(List.of()));

        StepVerifier.create(articleStatsService.getStatsBatch(List.of(ARTICLE_ID), List.of()))
            .assertNext(stats -> {
                assertThat(stats.getViews()).isEmpty();
                assertThat(stats.getFollows()).isEmpty();
                assertThat(stats.getCommentScores()).isEmpty();
            })
            .verifyComplete();

        verify(focusRepository, never()).countGroupByFocusIdIn(any());
    }
}
