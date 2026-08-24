package com.hcsy.spring.api.service.impl;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.function.Function;
import java.util.stream.Collectors;

import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.reactive.TransactionalOperator;

import com.hcsy.spring.api.repository.ArticleRepository;
import com.hcsy.spring.api.repository.CategoryRepository;
import com.hcsy.spring.api.repository.SubCategoryRepository;
import com.hcsy.spring.api.repository.UserRepository;
import com.hcsy.spring.api.service.ArticleService;
import com.hcsy.spring.common.constants.Defaults;
import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.exceptions.BusinessException;
import com.hcsy.spring.common.utils.EntityMapUtil;
import com.hcsy.spring.common.utils.Neo4jSyncMapUtil;
import com.hcsy.spring.core.annotation.ArticleSync;
import com.hcsy.spring.entity.dto.PageDTO;
import com.hcsy.spring.entity.po.Article;
import com.hcsy.spring.entity.po.Category;
import com.hcsy.spring.entity.po.SubCategory;
import com.hcsy.spring.entity.po.User;
import com.hcsy.spring.entity.vo.ArticleWithCategoryVO;
import com.hcsy.spring.entity.vo.IdCountVO;

import cn.hutool.core.bean.BeanUtil;
import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

@Service
@RequiredArgsConstructor
public class ArticleServiceImpl implements ArticleService {

    private final ArticleRepository articleRepository;
    private final UserRepository userRepository;
    private final SubCategoryRepository subCategoryRepository;
    private final CategoryRepository categoryRepository;
    private final TransactionalOperator transactionalOperator;

    @Override
    public Flux<Article> listPublishedArticles() {
        return articleRepository.findByStatusOrderByCreateAtAsc(1);
    }

    @Override
    public Mono<PageDTO<Article>> listPublishedArticles(long page, long size) {
        PageRequest pageable = pageRequest(page, size);
        return toPage(page, size,
            articleRepository.findByStatusOrderByCreateAtAsc(1, pageable).collectList(),
            articleRepository.countByStatus(1));
    }

    @Override
    @ArticleSync(action = "add", description = "创建了1篇文章")
    public Mono<Boolean> saveArticle(Article article) {
        return transactionalOperator.transactional(articleRepository.save(article)).thenReturn(true);
    }

    @Override
    @ArticleSync(action = "edit", description = "编辑了1篇文章")
    public Mono<Boolean> updateArticle(Article article) {
        return transactionalOperator.transactional(
            articleRepository.updateArticle(
                article.getId(),
                article.getTitle(),
                article.getContent(),
                article.getUserId(),
                article.getTags(),
                article.getStatus(),
                article.getSubCategoryId(),
                article.getUpdateAt()))
            .thenReturn(true);
    }

    @Override
    @ArticleSync(action = "delete", description = "删除了1篇文章")
    public Mono<Boolean> deleteArticle(Long id) {
        Mono<Void> operation = articleRepository.findById(id)
            .switchIfEmpty(Mono.error(notFound(Messages.UNDEFINED_ARTICLE_ID + id)))
            .flatMap(articleRepository::delete);
        return transactionalOperator.transactional(operation).thenReturn(true);
    }

    @Override
    @ArticleSync(action = "delete", description = "批量删除文章")
    public Mono<Boolean> deleteArticles(List<Long> ids) {
        List<Long> distinctIds = normalizeIds(ids);
        if (distinctIds.isEmpty()) {
            return Mono.just(true);
        }
        Mono<Void> operation = articleRepository.findAllById(distinctIds)
            .count()
            .filter(count -> count == distinctIds.size())
            .switchIfEmpty(Mono.error(notFound(Messages.UNDEFINED_ARTICLES)))
            .then(articleRepository.deleteAllById(distinctIds));
        return transactionalOperator.transactional(operation).thenReturn(true);
    }

    @Override
    public Mono<PageDTO<Article>> listArticlesById(long page, long size, Long id, boolean onlyPublished) {
        PageRequest pageable = pageRequest(page, size);
        if (onlyPublished) {
            return toPage(page, size,
                articleRepository.findByUserIdAndStatusOrderByCreateAtAsc(id, 1, pageable).collectList(),
                articleRepository.countByUserIdAndStatus(id, 1));
        }
        return toPage(page, size,
            articleRepository.findByUserIdOrderByCreateAtAsc(id, pageable).collectList(),
            articleRepository.countByUserId(id));
    }

    @Override
    public Mono<PageDTO<ArticleWithCategoryVO>> listArticlesByIdWithCategory(
        long page, long size, Long id, boolean onlyPublished) {
        return listArticlesById(page, size, id, onlyPublished).flatMap(this::toArticleVoPage);
    }

    @Override
    @ArticleSync(action = "publish", description = "发布了1篇文章")
    public Mono<Void> publishArticle(Long id) {
        Mono<Void> operation = articleRepository.findById(id)
            .switchIfEmpty(Mono.error(notFound(Messages.UNDEFINED_ARTICLE)))
            .then(articleRepository.publishById(id))
            .filter(updated -> updated > 0)
            .switchIfEmpty(Mono.error(unprocessable(Messages.PUBLISH_ARTICLE)))
            .then();
        return transactionalOperator.transactional(operation);
    }

    @Override
    @ArticleSync(action = "view", description = "浏览了1篇文章")
    public Mono<Void> addViewArticle(Long id) {
        Mono<Void> operation = articleRepository.findById(id)
            .switchIfEmpty(Mono.error(notFound(Messages.UNDEFINED_ARTICLE)))
            .flatMap(article -> {
                if (!Integer.valueOf(1).equals(article.getStatus())) {
                    return Mono.error(unprocessable(Messages.UNPUBLISH_ADD_VIEW));
                }
                return articleRepository.incrementViews(id);
            })
            .filter(updated -> updated > 0)
            .switchIfEmpty(Mono.error(unprocessable(Messages.ADD_VIEW_ARTICLE)))
            .then();
        return transactionalOperator.transactional(operation);
    }

    @Override
    public Flux<Article> listUnpublishedArticles() {
        return articleRepository.findByStatusOrderByCreateAtAsc(0);
    }

    @Override
    public Mono<PageDTO<Article>> listUnpublishedArticles(long page, long size) {
        PageRequest pageable = pageRequest(page, size);
        return toPage(page, size,
            articleRepository.findByStatusOrderByCreateAtAsc(0, pageable).collectList(),
            articleRepository.countByStatus(0));
    }

    @Override
    public Mono<PageDTO<ArticleWithCategoryVO>> listUnpublishedArticlesWithCategory(long page, long size) {
        return listUnpublishedArticles(page, size).flatMap(this::toArticleVoPage);
    }

    @Override
    public Mono<Article> findByArticleTitle(String articleTitle) {
        return articleRepository.findFirstByTitle(articleTitle);
    }

    @Override
    public Flux<Article> listAllArticlesByTitle(String articleTitle) {
        return articleRepository.findByTitleContaining(articleTitle);
    }

    @Override
    public Mono<Article> getById(Long id) {
        return articleRepository.findById(id);
    }

    @Override
    public Flux<Article> listByIds(Collection<Long> ids) {
        return articleRepository.findAllById(ids);
    }

    @Override
    public Mono<List<IdCountVO>> getArticleViewsByIDs(Collection<Long> ids) {
        if (ids == null || ids.isEmpty()) {
            return Mono.just(List.of());
        }
        return articleRepository.findAllById(ids)
            .map(article -> new IdCountVO(article.getId(), article.getViews() == null ? 0L : article.getViews().longValue()))
            .collectList();
    }

    @Override
    public Mono<Long> getTotalArticles() {
        return articleRepository.count();
    }

    private Mono<PageDTO<ArticleWithCategoryVO>> toArticleVoPage(PageDTO<Article> source) {
        List<Article> records = source.getRecords();
        if (records == null || records.isEmpty()) {
            return Mono.just(page(source.getCurrent(), source.getSize(), source.getTotal(), Collections.emptyList()));
        }

        Set<Long> userIds = records.stream().map(Article::getUserId).filter(id -> id != null)
            .collect(Collectors.toSet());
        Set<Long> subCategoryIds = records.stream().map(Article::getSubCategoryId).filter(id -> id != null)
            .map(Integer::longValue).collect(Collectors.toSet());

        Mono<Map<Long, User>> users = userRepository.findAllById(userIds)
            .collectMap(User::getId, Function.identity());
        Mono<Map<Long, SubCategory>> subCategories = subCategoryRepository.findAllById(subCategoryIds)
            .collectMap(SubCategory::getId, Function.identity());

        return Mono.zip(users, subCategories).flatMap(relations -> {
            Map<Long, SubCategory> subCategoryMap = relations.getT2();
            Set<Long> categoryIds = subCategoryMap.values().stream().map(SubCategory::getCategoryId)
                .filter(id -> id != null).collect(Collectors.toSet());
            return categoryRepository.findAllById(categoryIds)
                .collectMap(Category::getId, Function.identity())
                .map(categories -> mapArticlePage(source, relations.getT1(), subCategoryMap, categories));
        });
    }

    private PageDTO<ArticleWithCategoryVO> mapArticlePage(
        PageDTO<Article> source,
        Map<Long, User> users,
        Map<Long, SubCategory> subCategories,
        Map<Long, Category> categories) {
        List<ArticleWithCategoryVO> records = source.getRecords().stream().map(article -> {
            ArticleWithCategoryVO vo = BeanUtil.copyProperties(article, ArticleWithCategoryVO.class);
            User user = users.get(article.getUserId());
            vo.setUsername(user == null ? Defaults.DEFAULT_USER : user.getName());
            if (article.getSubCategoryId() != null) {
                SubCategory subCategory = subCategories.get(article.getSubCategoryId().longValue());
                if (subCategory != null) {
                    vo.setSubCategoryName(subCategory.getName());
                    Category category = categories.get(subCategory.getCategoryId());
                    if (category != null) {
                        vo.setCategoryId(category.getId());
                        vo.setCategoryName(category.getName());
                    }
                }
            }
            return vo;
        }).toList();
        return page(source.getCurrent(), source.getSize(), source.getTotal(), records);
    }

    private <T> Mono<PageDTO<T>> toPage(long current, long size, Mono<List<T>> records, Mono<Long> total) {
        return Mono.zip(records, total).map(result -> page(current, size, result.getT2(), result.getT1()));
    }

    private <T> PageDTO<T> page(long current, long size, long total, List<T> records) {
        PageDTO<T> result = new PageDTO<>();
        result.setCurrent(current);
        result.setSize(size);
        result.setTotal(total);
        result.setRecords(records);
        return result;
    }

    private PageRequest pageRequest(long page, long size) {
        return PageRequest.of((int) Math.max(0, page - 1), (int) Math.max(1, Math.min(size, 1000)));
    }

    private List<Long> normalizeIds(List<Long> ids) {
        return ids == null ? List.of() : ids.stream().filter(id -> id != null).distinct().toList();
    }

    private BusinessException notFound(String message) {
        return BusinessException.builder().httpStatus(HttpCode.NOT_FOUND).errorMessage(message).build();
    }

    private BusinessException unprocessable(String message) {
        return BusinessException.builder().httpStatus(HttpCode.UNPROCESSABLE_ENTITY).errorMessage(message).build();
    }

    // ==================== 统计方法 ====================

    @Override
    public Mono<Integer> getTotalViews() {
        return articleRepository.findAll()
            .map(article -> article.getViews() != null ? article.getViews() : 0)
            .reduce(0, Integer::sum);
    }

    @Override
    public Mono<Long> getActiveAuthors() {
        return articleRepository.countDistinctUserId().defaultIfEmpty(0L);
    }

    @Override
    public Mono<Double> getAverageViews() {
        return articleRepository.findAll()
            .map(article -> article.getViews() != null ? article.getViews() : 0)
            .collectList()
            .map(views -> {
                if (views.isEmpty()) {
                    return 0.0;
                }
                double sum = views.stream().mapToInt(Integer::intValue).sum();
                return Math.round(sum / views.size() * 100.0) / 100.0;
            });
    }

    @Override
    public Mono<List<Map<String, Object>>> getArticlesForExcelExport() {
        return articleRepository.findArticlesForExcelExport()
            .map(row -> {
                Map<String, Object> map = new HashMap<>();
                map.put("id", row.getId());
                map.put("title", row.getTitle());
                map.put("content", row.getContent());
                map.put("user_id", row.getUser_id());
                map.put("username", row.getUsername());
                map.put("tags", row.getTags());
                map.put("status", row.getStatus());
                map.put("create_at", row.getCreate_at());
                map.put("update_at", row.getUpdate_at());
                map.put("views", row.getViews());
                map.put("sub_category_id", row.getSub_category_id());
                map.put("sub_category_name", row.getSub_category_name());
                map.put("category_id", row.getCategory_id());
                map.put("category_name", row.getCategory_name());
                map.put("like_count", row.getLike_count());
                map.put("collect_count", row.getCollect_count());
                return map;
            })
            .collectList()
            .map(list -> list.isEmpty() ? new ArrayList<>() : list);
    }

    @Override
    public Mono<List<Map<String, Object>>> getTop10Articles() {
        return articleRepository.findTop10ByStatusOrderByViewsDesc(1)
            .map(EntityMapUtil::articleToMap)
            .collectList()
            .map(list -> list.isEmpty() ? new ArrayList<>() : list);
    }

    @Override
    public Mono<List<Map<String, Object>>> getCategoryArticleCount() {
        return articleRepository.countBySubCategoryIdGroupBy()
            .map(row -> {
                Map<String, Object> map = new HashMap<>();
                map.put("sub_category_id", row.getSubCategoryId());
                map.put("count", row.getCount());
                return map;
            })
            .collectList()
            .map(list -> list.isEmpty() ? new ArrayList<>() : list);
    }

    @Override
    public Mono<List<Map<String, Object>>> getMonthlyPublishCount() {
        return articleRepository.countMonthlyPublished()
            .map(row -> {
                Map<String, Object> map = new HashMap<>();
                map.put("year_month", row.getYearMonth());
                map.put("count", row.getCount());
                return map;
            })
            .collectList()
            .map(list -> list.isEmpty() ? new ArrayList<>() : list);
    }

    @Override
    public Mono<List<Map<String, Object>>> getNeo4jSyncArticles(String updatedAfter) {
        if (updatedAfter == null || updatedAfter.isBlank()) {
            return articleRepository.findAll()
                .map(Neo4jSyncMapUtil::articleToMap)
                .collectList()
                .map(list -> list.isEmpty() ? new ArrayList<>() : list);
        }
        LocalDateTime after = LocalDateTime.parse(updatedAfter);
        return articleRepository.findByUpdateAtAfter(after)
            .map(Neo4jSyncMapUtil::articleToMap)
            .collectList()
            .map(list -> list.isEmpty() ? new ArrayList<>() : list);
    }
}
