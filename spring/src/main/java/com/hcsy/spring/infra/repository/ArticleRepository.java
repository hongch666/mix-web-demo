package com.hcsy.spring.infra.repository;

import java.time.LocalDateTime;

import org.springframework.data.domain.Pageable;
import org.springframework.data.r2dbc.repository.Modifying;
import org.springframework.data.r2dbc.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.data.repository.reactive.ReactiveCrudRepository;

import com.hcsy.spring.entity.po.Article;
import com.hcsy.spring.entity.projection.ArticleExcelRow;
import com.hcsy.spring.entity.vo.CategoryCountVO;
import com.hcsy.spring.entity.vo.MonthlyCountVO;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

/**
 * 负责文章实体（Article）的响应式数据访问，含发布、浏览计数、排行统计与 Excel 导出查询
 */
public interface ArticleRepository extends ReactiveCrudRepository<Article, Long> {
    /**
     * 按创建时间升序查询指定状态（如已发布）的文章列表
     */
    Flux<Article> findByStatusOrderByCreateAtAsc(Integer status);

    /**
     * 按创建时间升序分页查询指定状态的文章列表
     */
    Flux<Article> findByStatusOrderByCreateAtAsc(Integer status, Pageable pageable);

    /**
     * 统计指定状态的文章总数
     */
    Mono<Long> countByStatus(Integer status);

    /**
     * 按创建时间升序分页查询指定用户发布的文章列表
     */
    Flux<Article> findByUserIdOrderByCreateAtAsc(Long userId, Pageable pageable);

    /**
     * 统计指定用户发布的文章总数
     */
    Mono<Long> countByUserId(Long userId);

    /**
     * 按创建时间升序分页查询指定用户处于指定状态的文章列表
     */
    Flux<Article> findByUserIdAndStatusOrderByCreateAtAsc(Long userId, Integer status, Pageable pageable);

    /**
     * 统计指定用户处于指定状态的文章数量
     */
    Mono<Long> countByUserIdAndStatus(Long userId, Integer status);

    /**
     * 按标题精确查找第一篇文章，用于创建文章时校验标题是否重复
     */
    Mono<Article> findFirstByTitle(String title);

    /**
     * 按标题模糊查询文章列表
     */
    Flux<Article> findByTitleContaining(String title);

    /**
     * 将指定文章状态更新为已发布，用于文章发布操作
     */
    @Modifying
    @Query("UPDATE articles SET status = 1 WHERE id = :id")
    Mono<Integer> publishById(@Param("id") Long id);

    /**
     * 对已发布文章的浏览量原子加一，用于浏览计数
     */
    @Modifying
    @Query("UPDATE articles SET views = views + 1, update_at = update_at WHERE id = :id AND status = 1")
    Mono<Integer> incrementViews(@Param("id") Long id);

    /**
     * 按主键更新文章标题、内容、标签、状态与子分类并刷新更新时间
     */
    @Modifying
    @Query("UPDATE articles SET title = :title, content = :content, user_id = :userId, "
        + "tags = :tags, status = :status, sub_category_id = :subCategoryId, "
        + "update_at = :updateAt WHERE id = :id")
    Mono<Integer> updateArticle(@Param("id") Long id,
        @Param("title") String title,
        @Param("content") String content,
        @Param("userId") Long userId,
        @Param("tags") String tags,
        @Param("status") Integer status,
        @Param("subCategoryId") Integer subCategoryId,
        @Param("updateAt") LocalDateTime updateAt);

    /**
     * 统计发布过文章的去重作者数量，用于活跃作者指标
     */
    @Query("SELECT COUNT(DISTINCT user_id) FROM articles")
    Mono<Long> countDistinctUserId();

    /**
     * 查询指定状态下浏览量最高的前 10 篇文章，用于热门文章排行
     */
    Flux<Article> findTop10ByStatusOrderByViewsDesc(Integer status);

    /**
     * 多表 JOIN 查询文章及其作者、分类、点赞数与收藏数，返回 Excel 导出投影行
     */
    @Query("""
        SELECT a.id AS id, a.title AS title, a.content AS content, a.user_id AS user_id,
               u.name AS username, a.tags AS tags, a.status AS status,
               a.create_at AS create_at, a.update_at AS update_at, a.views AS views,
               a.sub_category_id AS sub_category_id, sc.name AS sub_category_name,
               c.id AS category_id, c.name AS category_name,
               (SELECT COUNT(*) FROM likes l WHERE l.article_id = a.id) AS like_count,
               (SELECT COUNT(*) FROM collects cl WHERE cl.article_id = a.id) AS collect_count
        FROM articles a
        LEFT JOIN user u ON a.user_id = u.id
        LEFT JOIN sub_category sc ON a.sub_category_id = sc.id
        LEFT JOIN category c ON sc.category_id = c.id
        ORDER BY a.id
        """)
    Flux<ArticleExcelRow> findArticlesForExcelExport();

    /**
     * 按子分类分组统计已发布文章数量并按数量降序返回，用于分类文章计数
     */
    @Query("""
        SELECT sub_category_id AS subCategoryId, COUNT(*) AS count
        FROM articles
        WHERE status = 1
        GROUP BY sub_category_id
        ORDER BY count DESC
        """)
    Flux<CategoryCountVO> countBySubCategoryIdGroupBy();

    /**
     * 按月分组统计近 24 个月已发布文章数量并按月份倒序返回，用于发布趋势统计
     */
    @Query("""
        SELECT DATE_FORMAT(create_at, '%Y-%m') AS yearMonth, COUNT(*) AS count
        FROM articles
        WHERE status = 1 AND create_at >= DATE_SUB(NOW(), INTERVAL 24 MONTH)
        GROUP BY yearMonth
        ORDER BY yearMonth DESC
        """)
    Flux<MonthlyCountVO> countMonthlyPublished();

    /**
     * 查询 update_at > :after 的文章，用于Neo4j增量同步
     */
    @Query("SELECT * FROM articles WHERE update_at > :after")
    Flux<Article> findByUpdateAtAfter(@Param("after") LocalDateTime after);
}
