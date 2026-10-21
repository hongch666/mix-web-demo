package com.hcsy.spring.application.service.impl;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.function.Function;
import java.util.stream.Collectors;

import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.reactive.TransactionalOperator;

import com.hcsy.spring.application.service.ArticleService;
import com.hcsy.spring.common.constants.Defaults;
import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.exceptions.BusinessException;
import com.hcsy.spring.entity.dto.ArticleCreateDTO;
import com.hcsy.spring.entity.dto.ArticleUpdateDTO;
import com.hcsy.spring.entity.dto.PageDTO;
import com.hcsy.spring.entity.po.Article;
import com.hcsy.spring.entity.po.Category;
import com.hcsy.spring.entity.po.SubCategory;
import com.hcsy.spring.entity.po.User;
import com.hcsy.spring.entity.vo.ArticleExportVO;
import com.hcsy.spring.entity.vo.ArticleSyncVO;
import com.hcsy.spring.entity.vo.ArticleWithCategoryVO;
import com.hcsy.spring.entity.vo.CategoryArticleCountVO;
import com.hcsy.spring.entity.vo.IdCountVO;
import com.hcsy.spring.entity.vo.MonthlyPublishCountVO;
import com.hcsy.spring.infra.repository.ArticleRepository;
import com.hcsy.spring.infra.repository.CategoryRepository;
import com.hcsy.spring.infra.repository.SubCategoryRepository;
import com.hcsy.spring.infra.repository.UserRepository;

import cn.hutool.core.bean.BeanUtil;
import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

/**
 * ArticleService 的实现，基于 R2DBC 仓储在事务中完成文章创建更新删除、发布与阅读量处理、分页与标题检索及各类统计指标查询
 */
@Service
@RequiredArgsConstructor
public class ArticleServiceImpl implements ArticleService {

    private final ArticleRepository articleRepository;
    private final UserRepository userRepository;
    private final SubCategoryRepository subCategoryRepository;
    private final CategoryRepository categoryRepository;
    private final TransactionalOperator transactionalOperator;

    /**
     * 实现查询所有已发布文章并以 Flux 流式返回
     */
    @Override
    public Flux<Article> listPublishedArticles() {
        return articleRepository.findByStatusOrderByCreateAtAsc(1);
    }

    /**
     * 实现分页查询已发布文章
     */
    @Override
    public Mono<PageDTO<Article>> listPublishedArticles(long page, long size) {
        PageRequest pageable = pageRequest(page, size);
        return toPage(page, size,
            articleRepository.findByStatusOrderByCreateAtAsc(1, pageable).collectList(),
            articleRepository.countByStatus(1));
    }

    /**
     * 实现在事务中保存文章并返回带主键的实体供精确同步
     */
    @Override
    public Mono<Article> saveArticle(Article article) {
        // 返回保存后的实体，便于上层把新增文章主键用于精确同步
        return transactionalOperator.transactional(articleRepository.save(article));
    }

    /**
     * 实现根据用户名解析作者后创建文章，初始阅读量为0
     */
    @Override
    public Mono<Article> createArticle(ArticleCreateDTO dto) {
        return userRepository.findByName(dto.getUsername())
            .flatMap(user -> {
                Article article = BeanUtil.copyProperties(dto, Article.class);
                article.setUserId(user.getId());
                article.setViews(0);
                return saveArticle(article);
            });
    }

    /**
     * 实现根据用户名解析作者并更新文章与更新时间
     */
    @Override
    public Mono<Boolean> updateArticle(ArticleUpdateDTO dto) {
        return userRepository.findByName(dto.getUsername())
            .flatMap(user -> {
                Article article = BeanUtil.copyProperties(dto, Article.class);
                article.setUserId(user.getId());
                article.setUpdateAt(LocalDateTime.now());
                return updateArticle(article);
            });
    }

    /**
     * 实现查询文章详情并补充作者用户名，无作者时用默认用户
     */
    @Override
    public Mono<ArticleWithCategoryVO> getArticleDetail(Long id) {
        return getById(id).flatMap(article -> {
            ArticleWithCategoryVO vo = BeanUtil.copyProperties(article, ArticleWithCategoryVO.class);
            if (article.getUserId() == null) {
                vo.setUsername(Defaults.DEFAULT_USER);
                return Mono.just(vo);
            }
            return userRepository.findById(article.getUserId())
                .map(user -> {
                    vo.setUsername(user.getName());
                    return vo;
                })
                .defaultIfEmpty(vo);
        });
    }

    /**
     * 实现按ID批量查询文章并转为视图对象列表
     */
    @Override
    public Mono<List<ArticleWithCategoryVO>> getArticleDetailsByIds(Collection<Long> ids) {
        return listByIds(ids).map(article -> BeanUtil.copyProperties(article, ArticleWithCategoryVO.class))
            .collectList();
    }

    /**
     * 实现按标题模糊查询文章并转为视图对象列表
     */
    @Override
    public Mono<List<ArticleWithCategoryVO>> getArticleDetailsByTitle(String title) {
        return listAllArticlesByTitle(title)
            .map(article -> BeanUtil.copyProperties(article, ArticleWithCategoryVO.class))
            .collectList();
    }

    /**
     * 实现在事务中按字段更新文章，成功返回 true
     */
    @Override
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

    /**
     * 实现删除指定文章，文章不存在时抛出404业务异常
     */
    @Override
    public Mono<Boolean> deleteArticle(Long id) {
        Mono<Void> operation = articleRepository.findById(id)
            .switchIfEmpty(Mono.error(notFound(Messages.UNDEFINED_ARTICLE_ID + id)))
            .flatMap(articleRepository::delete);
        return transactionalOperator.transactional(operation).thenReturn(true);
    }

    /**
     * 实现批量删除文章，任一ID不存在时抛出404业务异常
     */
    @Override
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

    /**
     * 实现分页查询指定用户的文章，可仅看已发布
     */
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

    /**
     * 实现分页查询指定用户文章并转换为带分类视图
     */
    @Override
    public Mono<PageDTO<ArticleWithCategoryVO>> listArticlesByIdWithCategory(
        long page, long size, Long id, boolean onlyPublished) {
        return listArticlesById(page, size, id, onlyPublished).flatMap(this::toArticleVoPage);
    }

    /**
     * 实现发布文章，文章不存在或更新行数为0时抛出业务异常
     */
    @Override
    public Mono<Void> publishArticle(Long id) {
        Mono<Void> operation = articleRepository.findById(id)
            .switchIfEmpty(Mono.error(notFound(Messages.UNDEFINED_ARTICLE)))
            .then(articleRepository.publishById(id))
            .filter(updated -> updated > 0)
            .switchIfEmpty(Mono.error(unprocessable(Messages.PUBLISH_ARTICLE)))
            .then();
        return transactionalOperator.transactional(operation);
    }

    /**
     * 实现为已发布文章增加阅读量，未发布或更新失败时抛出业务异常
     */
    @Override
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

    /**
     * 实现查询所有未发布文章并以 Flux 流式返回
     */
    @Override
    public Flux<Article> listUnpublishedArticles() {
        return articleRepository.findByStatusOrderByCreateAtAsc(0);
    }

    /**
     * 实现分页查询未发布文章
     */
    @Override
    public Mono<PageDTO<Article>> listUnpublishedArticles(long page, long size) {
        PageRequest pageable = pageRequest(page, size);
        return toPage(page, size,
            articleRepository.findByStatusOrderByCreateAtAsc(0, pageable).collectList(),
            articleRepository.countByStatus(0));
    }

    /**
     * 实现分页查询未发布文章并转换为带分类视图
     */
    @Override
    public Mono<PageDTO<ArticleWithCategoryVO>> listUnpublishedArticlesWithCategory(long page, long size) {
        return listUnpublishedArticles(page, size).flatMap(this::toArticleVoPage);
    }

    /**
     * 实现按标题精确查找第一篇文章
     */
    @Override
    public Mono<Article> findByArticleTitle(String articleTitle) {
        return articleRepository.findFirstByTitle(articleTitle);
    }

    /**
     * 实现按标题模糊匹配并流式返回所有文章
     */
    @Override
    public Flux<Article> listAllArticlesByTitle(String articleTitle) {
        return articleRepository.findByTitleContaining(articleTitle);
    }

    /**
     * 实现按ID查询单篇文章
     */
    @Override
    public Mono<Article> getById(Long id) {
        return articleRepository.findById(id);
    }

    /**
     * 实现按ID批量流式查询文章
     */
    @Override
    public Flux<Article> listByIds(Collection<Long> ids) {
        return articleRepository.findAllById(ids);
    }

    /**
     * 实现批量查询多篇文章的阅读量，空阅读量按0处理
     */
    @Override
    public Mono<List<IdCountVO>> getArticleViewsByIDs(Collection<Long> ids) {
        if (ids == null || ids.isEmpty()) {
            return Mono.just(List.of());
        }
        return articleRepository.findAllById(ids)
            .map(article -> new IdCountVO(article.getId(),
                article.getViews() == null ? 0L : article.getViews().longValue()))
            .collectList();
    }

    /**
     * 实现统计文章总数
     */
    @Override
    public Mono<Long> getTotalArticles() {
        return articleRepository.count();
    }

    /**
     * 将文章分页结果批量补充作者与子分类、分类信息
     */
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

    /**
     * 将文章实体列表映射为带作者与分类名称的视图分页
     */
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

    /**
     * 合并记录与总数两个异步源并组装分页对象
     */
    private <T> Mono<PageDTO<T>> toPage(long current, long size, Mono<List<T>> records, Mono<Long> total) {
        return Mono.zip(records, total).map(result -> page(current, size, result.getT2(), result.getT1()));
    }

    /**
     * 组装分页结果的当前页、页大小、总数与记录
     */
    private <T> PageDTO<T> page(long current, long size, long total, List<T> records) {
        PageDTO<T> result = new PageDTO<>();
        result.setCurrent(current);
        result.setSize(size);
        result.setTotal(total);
        result.setRecords(records);
        return result;
    }

    /**
     * 构造分页请求，页码从1起始转0起始并限制每页最大1000条
     */
    private PageRequest pageRequest(long page, long size) {
        return PageRequest.of((int) Math.max(0, page - 1), (int) Math.max(1, Math.min(size, 1000)));
    }

    /**
     * 对ID列表去空并去重，空入参返回空列表
     */
    private List<Long> normalizeIds(List<Long> ids) {
        return ids == null ? List.of() : ids.stream().filter(id -> id != null).distinct().toList();
    }

    /**
     * 构造404资源不存在的业务异常
     */
    private BusinessException notFound(String message) {
        return BusinessException.builder().httpStatus(HttpCode.NOT_FOUND).errorMessage(message).build();
    }

    /**
     * 构造422不可处理实体的业务异常
     */
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

    /**
     * 实现统计有文章的活跃作者数
     */
    @Override
    public Mono<Long> getActiveAuthors() {
        return articleRepository.countDistinctUserId().defaultIfEmpty(0L);
    }

    /**
     * 实现计算所有文章的平均阅读量，结果保留两位小数
     */
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

    /**
     * 实现查询导出Excel所需的文章全量数据（含用户与分类关联列）
     */
    @Override
    public Mono<List<ArticleExportVO>> getArticlesForExcelExport() {
        return articleRepository.findArticlesForExcelExport()
            .map(row -> new ArticleExportVO(
                row.getId(), row.getTitle(), row.getContent(), row.getUser_id(), row.getUsername(),
                row.getTags(), row.getStatus(), row.getCreate_at(), row.getUpdate_at(), row.getViews(),
                row.getSub_category_id(), row.getSub_category_name(), row.getCategory_id(),
                row.getCategory_name(), row.getLike_count(), row.getCollect_count()))
            .collectList()
            .map(list -> list.isEmpty() ? new ArrayList<>() : list);
    }

    /**
     * 实现查询已发布阅读量最高的Top10文章并转为同步视图
     */
    @Override
    public Mono<List<ArticleSyncVO>> getTop10Articles() {
        return articleRepository.findTop10ByStatusOrderByViewsDesc(1)
            .map(this::articleToVO)
            .collectList()
            .map(list -> list.isEmpty() ? new ArrayList<>() : list);
    }

    /**
     * 文章实体转同步视图对象，用于内部接口返回通用数据
     */
    private ArticleSyncVO articleToVO(Article article) {
        return new ArticleSyncVO(
            article.getId(),
            article.getTitle(),
            article.getContent(),
            article.getUserId(),
            article.getTags(),
            article.getStatus(),
            article.getViews(),
            article.getSubCategoryId(),
            article.getCreateAt(),
            article.getUpdateAt());
    }

    /**
     * 实现按子分类分组统计文章数量
     */
    @Override
    public Mono<List<CategoryArticleCountVO>> getCategoryArticleCount() {
        return articleRepository.countBySubCategoryIdGroupBy()
            .map(row -> new CategoryArticleCountVO(row.getSubCategoryId(), row.getCount()))
            .collectList()
            .map(list -> list.isEmpty() ? new ArrayList<>() : list);
    }

    /**
     * 实现统计最近24个月每月发布文章数量
     */
    @Override
    public Mono<List<MonthlyPublishCountVO>> getMonthlyPublishCount() {
        return articleRepository.countMonthlyPublished()
            .map(row -> new MonthlyPublishCountVO(row.getYearMonth(), row.getCount()))
            .collectList()
            .map(list -> list.isEmpty() ? new ArrayList<>() : list);
    }

    /**
     * 实现查询文章数据用于Neo4j同步，支持按更新时间增量
     */
    @Override
    public Mono<List<ArticleSyncVO>> getNeo4jSyncArticles(String updatedAfter) {
        if (updatedAfter == null || updatedAfter.isBlank()) {
            return articleRepository.findAll()
                .map(this::articleToVO)
                .collectList()
                .map(list -> list.isEmpty() ? new ArrayList<>() : list);
        }
        LocalDateTime after = LocalDateTime.parse(updatedAfter);
        return articleRepository.findByUpdateAtAfter(after)
            .map(this::articleToVO)
            .collectList()
            .map(list -> list.isEmpty() ? new ArrayList<>() : list);
    }
}
