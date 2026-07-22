package com.hcsy.spring.api.service;

import java.util.Collection;
import java.util.List;

import com.hcsy.spring.entity.dto.PageDTO;
import com.hcsy.spring.entity.po.Article;
import com.hcsy.spring.entity.vo.ArticleWithCategoryVO;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

public interface ArticleService {
    Flux<Article> listPublishedArticles();

    Mono<PageDTO<Article>> listPublishedArticles(long page, long size);

    Mono<Boolean> saveArticle(Article article);

    Mono<Boolean> updateArticle(Article article);

    Mono<Boolean> deleteArticle(Long id);

    Mono<Boolean> deleteArticles(List<Long> ids);

    Mono<PageDTO<Article>> listArticlesById(long page, long size, Long id, boolean onlyPublished);

    Mono<PageDTO<ArticleWithCategoryVO>> listArticlesByIdWithCategory(
            long page, long size, Long id, boolean onlyPublished);

    Mono<Void> publishArticle(Long id);

    Mono<Void> addViewArticle(Long id);

    Flux<Article> listUnpublishedArticles();

    Mono<PageDTO<Article>> listUnpublishedArticles(long page, long size);

    Mono<PageDTO<ArticleWithCategoryVO>> listUnpublishedArticlesWithCategory(long page, long size);

    Mono<Article> findByArticleTitle(String articleTitle);

    Flux<Article> listAllArticlesByTitle(String articleTitle);

    Mono<Article> getById(Long id);

    Flux<Article> listByIds(Collection<Long> ids);
}
