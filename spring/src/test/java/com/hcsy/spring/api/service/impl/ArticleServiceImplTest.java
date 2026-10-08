package com.hcsy.spring.api.service.impl;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyIterable;
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
import org.springframework.data.domain.PageRequest;
import org.springframework.transaction.reactive.TransactionalOperator;

import com.hcsy.spring.api.repository.ArticleRepository;
import com.hcsy.spring.api.repository.CategoryRepository;
import com.hcsy.spring.api.repository.SubCategoryRepository;
import com.hcsy.spring.api.repository.UserRepository;
import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.exceptions.BusinessException;
import com.hcsy.spring.entity.po.Article;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

@ExtendWith(MockitoExtension.class)
class ArticleServiceImplTest {

    private static final Long ARTICLE_ID = 5L;
    private static final Long USER_ID = 9L;

    @Mock
    private ArticleRepository articleRepository;
    @Mock
    private UserRepository userRepository;
    @Mock
    private SubCategoryRepository subCategoryRepository;
    @Mock
    private CategoryRepository categoryRepository;
    @Mock
    private TransactionalOperator transactionalOperator;

    private ArticleServiceImpl articleService;

    @BeforeEach
    void setUp() {
        articleService = new ArticleServiceImpl(articleRepository, userRepository, subCategoryRepository,
            categoryRepository, transactionalOperator);
    }

    @Test
    @DisplayName("分页查询已发布文章时按页码与每页上限换算分页参数")
    void listPublishedArticlesNormalizesPageRequest() {
        when(articleRepository.findByStatusOrderByCreateAtAsc(1, PageRequest.of(0, 1000)))
            .thenReturn(Flux.just(article()));
        when(articleRepository.countByStatus(1)).thenReturn(Mono.just(1L));

        StepVerifier.create(articleService.listPublishedArticles(0, 5000))
            .assertNext(page -> {
                assertThat(page.getTotal()).isEqualTo(1L);
                assertThat(page.getRecords()).hasSize(1);
            })
            .verifyComplete();
    }

    @Test
    @DisplayName("删除不存在的文章返回未找到且不执行删除")
    void deleteArticleRejectsMissingArticle() {
        when(articleRepository.findById(ARTICLE_ID)).thenReturn(Mono.empty());
        stubTransactional();

        StepVerifier.create(articleService.deleteArticle(ARTICLE_ID))
            .expectErrorMatches(error -> isBusinessError(error, HttpCode.NOT_FOUND,
                Messages.UNDEFINED_ARTICLE_ID + ARTICLE_ID))
            .verify();

        verify(articleRepository, never()).delete(any(Article.class));
    }

    @Test
    @DisplayName("删除已存在的文章返回成功并执行删除")
    void deleteArticleRemovesExistingArticle() {
        Article article = article();
        when(articleRepository.findById(ARTICLE_ID)).thenReturn(Mono.just(article));
        when(articleRepository.delete(article)).thenReturn(Mono.empty());
        stubTransactional();

        StepVerifier.create(articleService.deleteArticle(ARTICLE_ID))
            .expectNext(true)
            .verifyComplete();

        verify(articleRepository).delete(article);
    }

    @Test
    @DisplayName("批量删除时空入参直接返回成功且不访问数据库")
    void deleteArticlesSkipsEmptyInput() {
        StepVerifier.create(articleService.deleteArticles(List.of())).expectNext(true).verifyComplete();
        StepVerifier.create(articleService.deleteArticles(null)).expectNext(true).verifyComplete();

        verify(transactionalOperator, never()).transactional(any(Mono.class));
        verify(articleRepository, never()).deleteAllById(anyIterable());
    }

    @Test
    @DisplayName("批量删除时存在不存在的文章则整体拒绝")
    void deleteArticlesRejectsPartiallyMissingArticles() {
        when(articleRepository.findAllById(List.of(1L, 2L))).thenReturn(Flux.just(article()));
        when(articleRepository.deleteAllById(List.of(1L, 2L))).thenReturn(Mono.empty());
        stubTransactional();

        StepVerifier.create(articleService.deleteArticles(List.of(1L, 2L)))
            .expectErrorMatches(error -> isBusinessError(error, HttpCode.NOT_FOUND, Messages.UNDEFINED_ARTICLES))
            .verify();

        verify(articleRepository).findAllById(List.of(1L, 2L));
    }

    @Test
    @DisplayName("发布不存在的文章返回未找到")
    void publishRejectsMissingArticle() {
        when(articleRepository.findById(ARTICLE_ID)).thenReturn(Mono.empty());
        when(articleRepository.publishById(ARTICLE_ID)).thenReturn(Mono.just(0));
        stubTransactional();

        StepVerifier.create(articleService.publishArticle(ARTICLE_ID))
            .expectErrorMatches(error -> isBusinessError(error, HttpCode.NOT_FOUND, Messages.UNDEFINED_ARTICLE))
            .verify();

        verify(articleRepository).findById(ARTICLE_ID);
    }

    @Test
    @DisplayName("发布时更新行数为零返回不可处理错误")
    void publishRejectsWhenNoRowUpdated() {
        when(articleRepository.findById(ARTICLE_ID)).thenReturn(Mono.just(article()));
        when(articleRepository.publishById(ARTICLE_ID)).thenReturn(Mono.just(0));
        stubTransactional();

        StepVerifier.create(articleService.publishArticle(ARTICLE_ID))
            .expectErrorMatches(error -> isBusinessError(error, HttpCode.UNPROCESSABLE_ENTITY,
                Messages.PUBLISH_ARTICLE))
            .verify();
    }

    @Test
    @DisplayName("增加阅读量时未发布文章返回不可处理错误且不更新")
    void addViewRejectsUnpublishedArticle() {
        Article article = article();
        article.setStatus(0);
        when(articleRepository.findById(ARTICLE_ID)).thenReturn(Mono.just(article));
        stubTransactional();

        StepVerifier.create(articleService.addViewArticle(ARTICLE_ID))
            .expectErrorMatches(error -> isBusinessError(error, HttpCode.UNPROCESSABLE_ENTITY,
                Messages.UNPUBLISH_ADD_VIEW))
            .verify();

        verify(articleRepository, never()).incrementViews(any());
    }

    @Test
    @DisplayName("增加阅读量成功时提交更新")
    void addViewIncrementsPublishedArticle() {
        when(articleRepository.findById(ARTICLE_ID)).thenReturn(Mono.just(article()));
        when(articleRepository.incrementViews(ARTICLE_ID)).thenReturn(Mono.just(1));
        stubTransactional();

        StepVerifier.create(articleService.addViewArticle(ARTICLE_ID)).verifyComplete();

        verify(articleRepository).incrementViews(ARTICLE_ID);
    }

    @Test
    @DisplayName("增加阅读量时更新行数为零返回不可处理错误")
    void addViewRejectsWhenNoRowUpdated() {
        when(articleRepository.findById(ARTICLE_ID)).thenReturn(Mono.just(article()));
        when(articleRepository.incrementViews(ARTICLE_ID)).thenReturn(Mono.just(0));
        stubTransactional();

        StepVerifier.create(articleService.addViewArticle(ARTICLE_ID))
            .expectErrorMatches(error -> isBusinessError(error, HttpCode.UNPROCESSABLE_ENTITY,
                Messages.ADD_VIEW_ARTICLE))
            .verify();
    }

    @Test
    @DisplayName("批量查询阅读量时空入参直接返回空列表")
    void getArticleViewsSkipsEmptyInput() {
        StepVerifier.create(articleService.getArticleViewsByIDs(List.of()))
            .assertNext(views -> assertThat(views).isEmpty())
            .verifyComplete();

        verify(articleRepository, never()).findAllById(anyIterable());
    }

    @Test
    @DisplayName("批量查询阅读量时空值按零返回")
    void getArticleViewsTreatsNullAsZero() {
        Article article = article();
        article.setViews(null);
        when(articleRepository.findAllById(List.of(ARTICLE_ID))).thenReturn(Flux.just(article));

        StepVerifier.create(articleService.getArticleViewsByIDs(List.of(ARTICLE_ID)))
            .assertNext(views -> {
                assertThat(views).hasSize(1);
                assertThat(views.get(0).getCount()).isZero();
            })
            .verifyComplete();
    }

    @Test
    @DisplayName("没有文章时平均阅读量返回零")
    void getAverageViewsReturnsZeroWhenEmpty() {
        when(articleRepository.findAll()).thenReturn(Flux.empty());

        StepVerifier.create(articleService.getAverageViews()).expectNext(0.0).verifyComplete();
    }

    @Test
    @DisplayName("平均阅读量按两位小数四舍五入")
    void getAverageViewsRoundsToTwoDecimals() {
        when(articleRepository.findAll()).thenReturn(Flux.just(articleWithViews(1), articleWithViews(2)));

        StepVerifier.create(articleService.getAverageViews()).expectNext(1.5).verifyComplete();
    }

    @Test
    @DisplayName("带分类的文章分页在无记录时不查询关联表")
    void listArticlesWithCategorySkipsRelationsWhenEmpty() {
        when(articleRepository.findByUserIdOrderByCreateAtAsc(USER_ID, PageRequest.of(0, 10)))
            .thenReturn(Flux.empty());
        when(articleRepository.countByUserId(USER_ID)).thenReturn(Mono.just(0L));

        StepVerifier.create(articleService.listArticlesByIdWithCategory(1, 10, USER_ID, false))
            .assertNext(page -> {
                assertThat(page.getRecords()).isEmpty();
                assertThat(page.getTotal()).isZero();
            })
            .verifyComplete();

        verify(userRepository, never()).findAllById(anyIterable());
    }

    private void stubTransactional() {
        when(transactionalOperator.transactional(any(Mono.class)))
            .thenAnswer(invocation -> invocation.getArgument(0));
    }

    private Article article() {
        Article article = new Article();
        article.setId(ARTICLE_ID);
        article.setUserId(USER_ID);
        article.setStatus(1);
        article.setViews(10);
        return article;
    }

    private Article articleWithViews(int views) {
        Article article = article();
        article.setViews(views);
        return article;
    }

    private boolean isBusinessError(Throwable error, int expectedStatus, String expectedMessage) {
        return error instanceof BusinessException businessException
            && businessException.getHttpStatus() == expectedStatus
            && expectedMessage.equals(businessException.getErrorMessage());
    }
}
