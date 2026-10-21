package com.hcsy.spring.application.service;

import java.util.Collection;
import java.util.List;

import com.hcsy.spring.entity.dto.ArticleCreateDTO;
import com.hcsy.spring.entity.dto.ArticleUpdateDTO;
import com.hcsy.spring.entity.dto.PageDTO;
import com.hcsy.spring.entity.po.Article;
import com.hcsy.spring.entity.vo.ArticleExportVO;
import com.hcsy.spring.entity.vo.ArticleSyncVO;
import com.hcsy.spring.entity.vo.ArticleWithCategoryVO;
import com.hcsy.spring.entity.vo.CategoryArticleCountVO;
import com.hcsy.spring.entity.vo.IdCountVO;
import com.hcsy.spring.entity.vo.MonthlyPublishCountVO;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

/**
 * 文章业务接口，定义文章增删改查、发布与阅读量处理、草稿与已发布分页查询、各类统计指标及Neo4j同步数据获取等响应式操作
 */
public interface ArticleService {
    /**
     * 查询所有已发布文章并以 Flux 流式返回
     */
    Flux<Article> listPublishedArticles();

    /**
     * 分页查询已发布文章
     */
    Mono<PageDTO<Article>> listPublishedArticles(long page, long size);

    /**
     * 保存文章并在事务中返回带主键的实体供精确同步
     */
    Mono<Article> saveArticle(Article article);

    /**
     * 根据创建DTO解析作者后新建文章，初始阅读量为0
     */
    Mono<Article> createArticle(ArticleCreateDTO dto);

    /**
     * 根据更新DTO解析作者并更新文章内容与更新时间
     */
    Mono<Boolean> updateArticle(ArticleUpdateDTO dto);

    /**
     * 查询单篇文章详情并补充作者用户名
     */
    Mono<ArticleWithCategoryVO> getArticleDetail(Long id);

    /**
     * 按ID批量查询文章并转为带作者信息的视图对象
     */
    Mono<List<ArticleWithCategoryVO>> getArticleDetailsByIds(Collection<Long> ids);

    /**
     * 按标题模糊查询文章并转为带作者信息的视图对象
     */
    Mono<List<ArticleWithCategoryVO>> getArticleDetailsByTitle(String title);

    /**
     * 在事务中按字段更新文章，成功返回 true
     */
    Mono<Boolean> updateArticle(Article article);

    /**
     * 删除指定文章，文章不存在时抛出404业务异常
     */
    Mono<Boolean> deleteArticle(Long id);

    /**
     * 批量删除文章，任一ID不存在时抛出404业务异常
     */
    Mono<Boolean> deleteArticles(List<Long> ids);

    /**
     * 分页查询指定用户的文章，可仅看已发布
     */
    Mono<PageDTO<Article>> listArticlesById(long page, long size, Long id, boolean onlyPublished);

    /**
     * 分页查询指定用户的文章并补充作者与分类信息
     */
    Mono<PageDTO<ArticleWithCategoryVO>> listArticlesByIdWithCategory(
        long page, long size, Long id, boolean onlyPublished);

    /**
     * 发布指定文章，文章不存在或发布失败时抛出业务异常
     */
    Mono<Void> publishArticle(Long id);

    /**
     * 为已发布文章增加阅读量，文章不存在或未发布时抛出业务异常
     */
    Mono<Void> addViewArticle(Long id);

    /**
     * 查询所有未发布（草稿）文章并以 Flux 流式返回
     */
    Flux<Article> listUnpublishedArticles();

    /**
     * 分页查询未发布（草稿）文章
     */
    Mono<PageDTO<Article>> listUnpublishedArticles(long page, long size);

    /**
     * 分页查询未发布文章并补充作者与分类信息
     */
    Mono<PageDTO<ArticleWithCategoryVO>> listUnpublishedArticlesWithCategory(long page, long size);

    /**
     * 按标题精确查找第一篇文章
     */
    Mono<Article> findByArticleTitle(String articleTitle);

    /**
     * 按标题模糊匹配并流式返回所有文章
     */
    Flux<Article> listAllArticlesByTitle(String articleTitle);

    /**
     * 按ID查询单篇文章
     */
    Mono<Article> getById(Long id);

    /**
     * 按ID批量流式查询文章
     */
    Flux<Article> listByIds(Collection<Long> ids);

    /**
     * 批量查询多篇文章的阅读量，返回ID与阅读量对
     */
    Mono<List<IdCountVO>> getArticleViewsByIDs(Collection<Long> ids);

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
    Mono<List<ArticleExportVO>> getArticlesForExcelExport();

    /**
     * 获取Top10文章（按阅读量降序）
     */
    Mono<List<ArticleSyncVO>> getTop10Articles();

    /**
     * 获取按子分类统计的文章数量
     */
    Mono<List<CategoryArticleCountVO>> getCategoryArticleCount();

    /**
     * 获取最近24个月文章发布数量统计
     */
    Mono<List<MonthlyPublishCountVO>> getMonthlyPublishCount();

    /**
     * 获取文章数据，用于Neo4j同步
     *
     * @param updatedAfter
     *                         增量同步时间（ISO格式），为空则全量
     */
    Mono<List<ArticleSyncVO>> getNeo4jSyncArticles(String updatedAfter);
}
