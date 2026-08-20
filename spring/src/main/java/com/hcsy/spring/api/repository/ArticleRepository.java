package com.hcsy.spring.api.repository;

import java.time.LocalDateTime;

import org.springframework.data.domain.Pageable;
import org.springframework.data.r2dbc.repository.Modifying;
import org.springframework.data.r2dbc.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.data.repository.reactive.ReactiveCrudRepository;

import com.hcsy.spring.entity.po.Article;
import com.hcsy.spring.entity.projection.ArticleExcelRow;
import com.hcsy.spring.entity.projection.CategoryCountRow;
import com.hcsy.spring.entity.projection.MonthlyCountRow;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

public interface ArticleRepository extends ReactiveCrudRepository<Article, Long> {
    Flux<Article> findByStatusOrderByCreateAtAsc(Integer status);

    Flux<Article> findByStatusOrderByCreateAtAsc(Integer status, Pageable pageable);

    Mono<Long> countByStatus(Integer status);

    Flux<Article> findByUserIdOrderByCreateAtAsc(Long userId, Pageable pageable);

    Mono<Long> countByUserId(Long userId);

    Flux<Article> findByUserIdAndStatusOrderByCreateAtAsc(Long userId, Integer status, Pageable pageable);

    Mono<Long> countByUserIdAndStatus(Long userId, Integer status);

    Mono<Article> findFirstByTitle(String title);

    Flux<Article> findByTitleContaining(String title);

    @Modifying
    @Query("UPDATE articles SET status = 1 WHERE id = :id")
    Mono<Integer> publishById(@Param("id") Long id);

    @Modifying
    @Query("UPDATE articles SET views = views + 1, update_at = update_at WHERE id = :id AND status = 1")
    Mono<Integer> incrementViews(@Param("id") Long id);

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

    @Query("SELECT COUNT(DISTINCT user_id) FROM articles")
    Mono<Long> countDistinctUserId();

    Flux<Article> findTop10ByStatusOrderByViewsDesc(Integer status);

    @Query("""
        SELECT a.id AS id, a.title AS title, a.content AS content, a.user_id AS user_id,
               u.name AS username, a.tags AS tags, a.status AS status,
               a.create_at AS create_at, a.update_at AS update_at, a.views AS views,
               a.sub_category_id AS sub_category_id, sc.name AS sub_category_name,
               c.id AS category_id, c.name AS category_name,
               (SELECT COUNT(*) FROM likes l WHERE l.article_id = a.id) AS like_count,
               (SELECT COUNT(*) FROM collects cl WHERE cl.article_id = a.id) AS collect_count
        FROM articles a
        LEFT JOIN users u ON a.user_id = u.id
        LEFT JOIN sub_categories sc ON a.sub_category_id = sc.id
        LEFT JOIN categories c ON sc.category_id = c.id
        ORDER BY a.id
        """)
    Flux<ArticleExcelRow> findArticlesForExcelExport();

    @Query("""
        SELECT sub_category_id AS subCategoryId, COUNT(*) AS count
        FROM articles
        WHERE status = 1
        GROUP BY sub_category_id
        ORDER BY count DESC
        """)
    Flux<CategoryCountRow> countBySubCategoryIdGroupBy();

    @Query("""
        SELECT DATE_FORMAT(create_at, '%Y-%m') AS yearMonth, COUNT(*) AS count
        FROM articles
        WHERE status = 1 AND create_at >= DATE_SUB(NOW(), INTERVAL 24 MONTH)
        GROUP BY yearMonth
        ORDER BY yearMonth DESC
        """)
    Flux<MonthlyCountRow> countMonthlyPublished();
}
