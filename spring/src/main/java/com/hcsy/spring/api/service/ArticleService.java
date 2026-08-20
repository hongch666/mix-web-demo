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

    Mono<java.util.Map<Long, Integer>> getArticleViewsByIDs(Collection<Long> ids);

    /**
     * 获取文章总数
     */
    Mono<Long> getTotalArticles();

    /**
     * 获取所有文章的总阅读量
     */
    Mono<Integer> getTotalViews();

    /**
     * 获取活跃作者数（有文章的用户数）
     */
    Mono<Long> getActiveAuthors();

    /**
     * 获取平均阅读次数
     */
    Mono<Double> getAverageViews();

    /**
     * 获取导出Excel所需文章数据
     */
    Mono<List<java.util.Map<String, Object>>> getArticlesForExcelExport();

    /**
     * 获取Top10文章（按阅读量降序）
     */
    Mono<List<java.util.Map<String, Object>>> getTop10Articles();

    /**
     * 获取按子分类统计的文章数量
     */
    Mono<List<java.util.Map<String, Object>>> getCategoryArticleCount();

    /**
     * 获取最近24个月文章发布数量统计
     */
    Mono<List<java.util.Map<String, Object>>> getMonthlyPublishCount();

    /**
     * 获取文章数据，用于Neo4j同步
     *
     * @param updatedAfter
     *                         增量同步时间（ISO格式），为空则全量
     */
    Mono<List<java.util.Map<String, Object>>> getNeo4jSyncArticles(String updatedAfter);
}
