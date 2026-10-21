package com.hcsy.spring.application.service.impl;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Collection;
import java.util.List;

import org.springframework.beans.BeanUtils;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.reactive.TransactionalOperator;

import com.hcsy.spring.application.service.CategoryService;
import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.constants.RedisKeys;
import com.hcsy.spring.common.exceptions.BusinessException;
import com.hcsy.spring.common.utils.CacheUtil;
import com.hcsy.spring.entity.dto.CategoryCreateDTO;
import com.hcsy.spring.entity.dto.CategoryUpdateDTO;
import com.hcsy.spring.entity.dto.PageDTO;
import com.hcsy.spring.entity.dto.SubCategoryCreateDTO;
import com.hcsy.spring.entity.dto.SubCategoryUpdateDTO;
import com.hcsy.spring.entity.po.Category;
import com.hcsy.spring.entity.po.SubCategory;
import com.hcsy.spring.entity.vo.CategorySyncVO;
import com.hcsy.spring.entity.vo.CategoryVO;
import com.hcsy.spring.entity.vo.SubCategorySyncVO;
import com.hcsy.spring.entity.vo.SubCategoryVO;
import com.hcsy.spring.entity.vo.SubCategoryWithParentVO;
import com.hcsy.spring.infra.repository.CategoryRepository;
import com.hcsy.spring.infra.repository.SubCategoryRepository;

import com.fasterxml.jackson.core.type.TypeReference;
import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

/**
 * CategoryService 的实现，在事务中维护分类与子分类并级联删除子分类，通过多级缓存加速分类查询并在写操作后失效缓存
 */
@Service
@RequiredArgsConstructor
public class CategoryServiceImpl implements CategoryService {
    private static final CacheUtil.CacheOptions<CategoryVO> CATEGORY_BY_ID_CACHE = CacheUtil.CacheOptions.fixed(
        RedisKeys.categoryByIdCacheName(), RedisKeys.categoryCacheInvalidationChannel(), 1_000);
    private static final CacheUtil.CacheOptions<PageDTO<CategoryVO>> CATEGORY_PAGE_CACHE = CacheUtil.CacheOptions.fixed(
        RedisKeys.categoryPageCacheName(), RedisKeys.categoryCacheInvalidationChannel(), 200);

    private final CategoryRepository categoryRepository;
    private final SubCategoryRepository subCategoryRepository;
    private final CacheUtil cacheUtil;
    private final TransactionalOperator transactionalOperator;

    /**
     * 实现新增分类并清除分类缓存
     */
    @Override
    public Mono<Long> addCategory(CategoryCreateDTO dto) {
        Category category = new Category();
        category.setName(dto.getName());
        return transactionalOperator.transactional(categoryRepository.save(category))
            .flatMap(saved -> evictAllCategoryCaches().thenReturn(saved.getId()));
    }

    /**
     * 实现更新分类名称，分类不存在时抛404异常
     */
    @Override
    public Mono<Void> updateCategory(CategoryUpdateDTO dto) {
        Mono<Void> databaseOperation = categoryRepository.findById(dto.getId())
            .switchIfEmpty(Mono.error(notFound(Messages.UNDEFINED_CATEGORY)))
            .flatMap(category -> {
                category.setName(dto.getName());
                return categoryRepository.save(category);
            })
            .then();
        return transactionalOperator.transactional(databaseOperation)
            .then(evictAllCategoryCaches());
    }

    /**
     * 实现在事务中删除分类并级联删除子分类，随后清缓存
     */
    @Override
    public Mono<Void> deleteCategory(Long id) {
        Mono<Void> databaseOperation = categoryRepository.findById(id)
            .switchIfEmpty(Mono.error(notFound(Messages.UNDEFINED_CATEGORY)))
            .flatMap(category -> subCategoryRepository.deleteByCategoryId(id)
                .then(categoryRepository.deleteById(id)));
        return transactionalOperator.transactional(databaseOperation)
            .then(evictAllCategoryCaches());
    }

    /**
     * 实现批量删除分类并级联删除各自子分类
     */
    @Override
    public Mono<Void> deleteCategories(List<Long> ids) {
        List<Long> distinctIds = normalizeIds(ids);
        if (distinctIds.isEmpty()) {
            return Mono.empty();
        }
        Mono<Void> databaseOperation = categoryRepository.findAllById(distinctIds)
            .count()
            .filter(count -> count == distinctIds.size())
            .switchIfEmpty(Mono.error(notFound(Messages.UNDEFINED_CATEGORIES)))
            .thenMany(Flux.fromIterable(distinctIds)
                .concatMap(id -> subCategoryRepository.deleteByCategoryId(id)
                    .then(categoryRepository.deleteById(id))))
            .then();
        return transactionalOperator.transactional(databaseOperation)
            .then(evictAllCategoryCaches());
    }

    /**
     * 实现新增子分类并清除分类缓存
     */
    @Override
    public Mono<Long> addSubCategory(SubCategoryCreateDTO dto) {
        SubCategory subCategory = new SubCategory();
        subCategory.setName(dto.getName());
        subCategory.setCategoryId(dto.getCategoryId());
        return transactionalOperator.transactional(subCategoryRepository.save(subCategory))
            .flatMap(saved -> evictAllCategoryCaches().thenReturn(saved.getId()));
    }

    /**
     * 实现更新子分类名称与所属分类，子分类不存在时抛404异常
     */
    @Override
    public Mono<Void> updateSubCategory(SubCategoryUpdateDTO dto) {
        Mono<Void> databaseOperation = subCategoryRepository.findById(dto.getId())
            .switchIfEmpty(Mono.error(notFound(Messages.UNDEFINED_SUB_CATEGORY)))
            .flatMap(subCategory -> {
                subCategory.setName(dto.getName());
                subCategory.setCategoryId(dto.getCategoryId());
                return subCategoryRepository.save(subCategory);
            })
            .then();
        return transactionalOperator.transactional(databaseOperation)
            .then(evictAllCategoryCaches());
    }

    /**
     * 实现删除指定子分类并清除分类缓存
     */
    @Override
    public Mono<Void> deleteSubCategory(Long id) {
        Mono<Void> databaseOperation = subCategoryRepository.findById(id)
            .switchIfEmpty(Mono.error(notFound(Messages.UNDEFINED_SUB_CATEGORY)))
            .flatMap(subCategoryRepository::delete);
        return transactionalOperator.transactional(databaseOperation)
            .then(evictAllCategoryCaches());
    }

    /**
     * 实现批量删除子分类，任一ID不存在时抛404异常
     */
    @Override
    public Mono<Void> deleteSubCategories(List<Long> ids) {
        List<Long> distinctIds = normalizeIds(ids);
        if (distinctIds.isEmpty()) {
            return Mono.empty();
        }
        Mono<Void> databaseOperation = subCategoryRepository.findAllById(distinctIds)
            .count()
            .filter(count -> count == distinctIds.size())
            .switchIfEmpty(Mono.error(notFound(Messages.UNDEFINED_SUB_CATEGORIES)))
            .then(subCategoryRepository.deleteAllById(distinctIds));
        return transactionalOperator.transactional(databaseOperation)
            .then(evictAllCategoryCaches());
    }

    /**
     * 实现查询分类详情含子分类列表，走多级缓存
     */
    @Override
    public Mono<CategoryVO> getCategoryById(Long id) {
        String cacheKey = RedisKeys.categoryId(id);
        return cacheUtil.get(CATEGORY_BY_ID_CACHE, id, cacheKey,
            CategoryVO.class, () -> loadCategory(id));
    }

    /**
     * 实现分页查询分类详情，走多级缓存
     */
    @Override
    public Mono<PageDTO<CategoryVO>> pageCategory(long page, long size) {
        String cacheKey = RedisKeys.categoryPage(page, size);
        return cacheUtil.get(CATEGORY_PAGE_CACHE, cacheKey, cacheKey,
            new TypeReference<PageDTO<CategoryVO>>() {
            }, () -> loadCategoryPage(page, size));
    }

    /**
     * 实现按ID批量流式查询分类
     */
    @Override
    public Flux<Category> listByIds(Collection<Long> ids) {
        return categoryRepository.findAllById(ids);
    }

    /**
     * 实现按ID批量流式查询子分类
     */
    @Override
    public Flux<SubCategory> listSubCategoriesByIds(Collection<Long> ids) {
        return subCategoryRepository.findAllById(ids);
    }

    /**
     * 缓存未命中时从数据库加载分类详情并组装子分类列表
     */
    private Mono<CategoryVO> loadCategory(Long id) {
        return categoryRepository.findById(id).flatMap(category -> {
            CategoryVO vo = new CategoryVO();
            BeanUtils.copyProperties(category, vo);
            return subCategoryRepository.findByCategoryIdOrderByIdAsc(category.getId())
                .map(subCategory -> {
                    SubCategoryVO subCategoryVO = new SubCategoryVO();
                    BeanUtils.copyProperties(subCategory, subCategoryVO);
                    return subCategoryVO;
                })
                .collectList()
                .map(subCategories -> {
                    vo.setSubCategories(subCategories);
                    return vo;
                });
        });
    }

    /**
     * 缓存未命中时从数据库加载分类分页并逐条填充子分类
     */
    private Mono<PageDTO<CategoryVO>> loadCategoryPage(long page, long size) {
        PageRequest pageable = PageRequest.of(toPageIndex(page), toPageSize(size));
        Mono<List<CategoryVO>> records = categoryRepository.findAllByOrderByIdAsc(pageable)
            .flatMapSequential(category -> loadCategory(category.getId()))
            .collectList();
        Mono<Long> total = categoryRepository.count();
        return Mono.zip(records, total).map(result -> {
            PageDTO<CategoryVO> pageDTO = new PageDTO<>();
            pageDTO.setCurrent(page);
            pageDTO.setSize(size);
            pageDTO.setTotal(result.getT2());
            pageDTO.setRecords(result.getT1());
            return pageDTO;
        });
    }

    /**
     * 清除分类详情与分类分页的全部本地与Redis缓存
     */
    private Mono<Void> evictAllCategoryCaches() {
        return cacheUtil.evictAll(RedisKeys.categoryAllPattern(), CATEGORY_BY_ID_CACHE, CATEGORY_PAGE_CACHE);
    }

    /**
     * 将1起始页码转换为0起始的分页索引，最小为0
     */
    private int toPageIndex(long page) {
        return (int) Math.max(0, page - 1);
    }

    /**
     * 将每页大小限制在1到1000之间
     */
    private int toPageSize(long size) {
        return (int) Math.max(1, Math.min(size, 1000));
    }

    /**
     * 对ID列表去空并去重，空入参返回空列表
     */
    private List<Long> normalizeIds(List<Long> ids) {
        if (ids == null) {
            return List.of();
        }
        return ids.stream().filter(id -> id != null).distinct().toList();
    }

    /**
     * 构造404资源不存在的业务异常
     */
    private BusinessException notFound(String message) {
        return BusinessException.builder().httpStatus(HttpCode.NOT_FOUND).errorMessage(message).build();
    }

    // ==================== 内部接口方法 ====================

    @Override
    public Flux<Category> listAllCategories() {
        return categoryRepository.findAll();
    }

    /**
     * 实现查询所有子分类并批量关联父分类名称，避免N+1查询
     */
    @Override
    public Flux<SubCategoryWithParentVO> listAllSubCategoriesWithParent() {
        return subCategoryRepository.findAll()
            .collectList()
            .flatMapMany(subCategories -> {
                // 收集所有分类ID，批量查询，避免 N+1 问题
                java.util.Set<Long> categoryIds = subCategories.stream()
                    .map(SubCategory::getCategoryId)
                    .collect(java.util.stream.Collectors.toSet());
                return categoryRepository.findAllById(categoryIds)
                    .collectMap(Category::getId, java.util.function.Function.identity())
                    .flatMapMany(categoryMap -> Flux.fromIterable(subCategories)
                        .map(subCategory -> {
                            Category category = categoryMap.get(subCategory.getCategoryId());
                            return new SubCategoryWithParentVO(
                                subCategory.getId(),
                                subCategory.getName(),
                                subCategory.getCategoryId(),
                                category != null ? category.getName() : Messages.UNCATEGORIZED,
                                subCategory.getCreateTime(),
                                subCategory.getUpdateTime());
                        }));
            });
    }

    /**
     * 实现查询分类数据用于Neo4j同步，支持按更新时间增量
     */
    @Override
    public Mono<List<CategorySyncVO>> getNeo4jSyncCategories(String updatedAfter) {
        if (updatedAfter == null || updatedAfter.isBlank()) {
            return categoryRepository.findAll()
                .map(this::categoryToVO)
                .collectList()
                .map(list -> list.isEmpty() ? new ArrayList<>() : list);
        }
        LocalDateTime after = LocalDateTime.parse(updatedAfter);
        return categoryRepository.findByUpdateTimeAfter(after)
            .map(this::categoryToVO)
            .collectList()
            .map(list -> list.isEmpty() ? new ArrayList<>() : list);
    }

    /**
     * 实现查询子分类数据用于Neo4j同步，支持按更新时间增量
     */
    @Override
    public Mono<List<SubCategorySyncVO>> getNeo4jSyncSubCategories(String updatedAfter) {
        if (updatedAfter == null || updatedAfter.isBlank()) {
            return subCategoryRepository.findAll()
                .map(this::subCategoryToVO)
                .collectList()
                .map(list -> list.isEmpty() ? new ArrayList<>() : list);
        }
        LocalDateTime after = LocalDateTime.parse(updatedAfter);
        return subCategoryRepository.findByUpdateTimeAfter(after)
            .map(this::subCategoryToVO)
            .collectList()
            .map(list -> list.isEmpty() ? new ArrayList<>() : list);
    }

    /**
     * 分类实体转同步视图对象，字段名与数据库列名保持一致，用于 Neo4j 同步
     */
    private CategorySyncVO categoryToVO(Category category) {
        return new CategorySyncVO(category.getId(), category.getName(), category.getUpdateTime());
    }

    /**
     * 子分类实体转同步视图对象，字段名与数据库列名保持一致，用于 Neo4j 同步
     */
    private SubCategorySyncVO subCategoryToVO(SubCategory subCategory) {
        return new SubCategorySyncVO(
            subCategory.getId(),
            subCategory.getName(),
            subCategory.getCategoryId(),
            subCategory.getUpdateTime());
    }
}
