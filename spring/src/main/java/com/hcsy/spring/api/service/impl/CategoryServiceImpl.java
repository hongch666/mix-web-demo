package com.hcsy.spring.api.service.impl;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Collection;
import java.util.List;

import org.springframework.beans.BeanUtils;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.reactive.TransactionalOperator;

import com.fasterxml.jackson.core.type.TypeReference;
import com.hcsy.spring.api.repository.CategoryRepository;
import com.hcsy.spring.api.repository.SubCategoryRepository;
import com.hcsy.spring.api.service.CategoryService;
import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.constants.RedisKeys;
import com.hcsy.spring.common.exceptions.BusinessException;
import com.hcsy.spring.common.utils.CacheUtil;
import com.hcsy.spring.common.utils.Neo4jSyncMapUtil;
import com.hcsy.spring.entity.dto.CategoryCreateDTO;
import com.hcsy.spring.entity.dto.CategoryUpdateDTO;
import com.hcsy.spring.entity.dto.PageDTO;
import com.hcsy.spring.entity.dto.SubCategoryCreateDTO;
import com.hcsy.spring.entity.dto.SubCategoryUpdateDTO;
import com.hcsy.spring.entity.po.Category;
import com.hcsy.spring.entity.po.SubCategory;
import com.hcsy.spring.entity.vo.CategoryVO;
import com.hcsy.spring.entity.vo.SubCategoryVO;

import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

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

    @Override
    public Mono<Long> addCategory(CategoryCreateDTO dto) {
        Category category = new Category();
        category.setName(dto.getName());
        return transactionalOperator.transactional(categoryRepository.save(category))
            .flatMap(saved -> evictAllCategoryCaches().thenReturn(saved.getId()));
    }

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

    @Override
    public Mono<Void> deleteCategory(Long id) {
        Mono<Void> databaseOperation = categoryRepository.findById(id)
            .switchIfEmpty(Mono.error(notFound(Messages.UNDEFINED_CATEGORY)))
            .flatMap(category -> subCategoryRepository.deleteByCategoryId(id)
                .then(categoryRepository.deleteById(id)));
        return transactionalOperator.transactional(databaseOperation)
            .then(evictAllCategoryCaches());
    }

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

    @Override
    public Mono<Long> addSubCategory(SubCategoryCreateDTO dto) {
        SubCategory subCategory = new SubCategory();
        subCategory.setName(dto.getName());
        subCategory.setCategoryId(dto.getCategoryId());
        return transactionalOperator.transactional(subCategoryRepository.save(subCategory))
            .flatMap(saved -> evictAllCategoryCaches().thenReturn(saved.getId()));
    }

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

    @Override
    public Mono<Void> deleteSubCategory(Long id) {
        Mono<Void> databaseOperation = subCategoryRepository.findById(id)
            .switchIfEmpty(Mono.error(notFound(Messages.UNDEFINED_SUB_CATEGORY)))
            .flatMap(subCategoryRepository::delete);
        return transactionalOperator.transactional(databaseOperation)
            .then(evictAllCategoryCaches());
    }

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

    @Override
    public Mono<CategoryVO> getCategoryById(Long id) {
        String cacheKey = RedisKeys.categoryId(id);
        return cacheUtil.get(CATEGORY_BY_ID_CACHE, id, cacheKey,
            CategoryVO.class, () -> loadCategory(id));
    }

    @Override
    public Mono<PageDTO<CategoryVO>> pageCategory(long page, long size) {
        String cacheKey = RedisKeys.categoryPage(page, size);
        return cacheUtil.get(CATEGORY_PAGE_CACHE, cacheKey, cacheKey,
            new TypeReference<PageDTO<CategoryVO>>() {
            }, () -> loadCategoryPage(page, size));
    }

    @Override
    public Flux<Category> listByIds(Collection<Long> ids) {
        return categoryRepository.findAllById(ids);
    }

    @Override
    public Flux<SubCategory> listSubCategoriesByIds(Collection<Long> ids) {
        return subCategoryRepository.findAllById(ids);
    }

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

    private Mono<Void> evictAllCategoryCaches() {
        return cacheUtil.evictAll(RedisKeys.categoryAllPattern(), CATEGORY_BY_ID_CACHE, CATEGORY_PAGE_CACHE);
    }

    private int toPageIndex(long page) {
        return (int) Math.max(0, page - 1);
    }

    private int toPageSize(long size) {
        return (int) Math.max(1, Math.min(size, 1000));
    }

    private List<Long> normalizeIds(List<Long> ids) {
        if (ids == null) {
            return List.of();
        }
        return ids.stream().filter(id -> id != null).distinct().toList();
    }

    private BusinessException notFound(String message) {
        return BusinessException.builder().httpStatus(HttpCode.NOT_FOUND).errorMessage(message).build();
    }

    // ==================== 内部接口方法 ====================

    @Override
    public Flux<Category> listAllCategories() {
        return categoryRepository.findAll();
    }

    @Override
    public Flux<java.util.Map<String, Object>> listAllSubCategoriesWithParent() {
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
                            java.util.Map<String, Object> map = new java.util.HashMap<>();
                            Category category = categoryMap.get(subCategory.getCategoryId());
                            map.put("id", subCategory.getId());
                            map.put("name", subCategory.getName());
                            map.put("category_id", subCategory.getCategoryId());
                            map.put("category_name", category != null ? category.getName() : Messages.UNCATEGORIZED);
                            map.put("create_time", subCategory.getCreateTime());
                            map.put("update_time", subCategory.getUpdateTime());
                            return map;
                        }));
            });
    }

    @Override
    public Mono<List<java.util.Map<String, Object>>> getNeo4jSyncCategories(String updatedAfter) {
        if (updatedAfter == null || updatedAfter.isBlank()) {
            return categoryRepository.findAll()
                .map(Neo4jSyncMapUtil::categoryToMap)
                .collectList()
                .map(list -> list.isEmpty() ? new ArrayList<>() : list);
        }
        LocalDateTime after = LocalDateTime.parse(updatedAfter);
        return categoryRepository.findByUpdateTimeAfter(after)
            .map(Neo4jSyncMapUtil::categoryToMap)
            .collectList()
            .map(list -> list.isEmpty() ? new ArrayList<>() : list);
    }

    @Override
    public Mono<List<java.util.Map<String, Object>>> getNeo4jSyncSubCategories(String updatedAfter) {
        if (updatedAfter == null || updatedAfter.isBlank()) {
            return subCategoryRepository.findAll()
                .map(Neo4jSyncMapUtil::subCategoryToMap)
                .collectList()
                .map(list -> list.isEmpty() ? new ArrayList<>() : list);
        }
        LocalDateTime after = LocalDateTime.parse(updatedAfter);
        return subCategoryRepository.findByUpdateTimeAfter(after)
            .map(Neo4jSyncMapUtil::subCategoryToMap)
            .collectList()
            .map(list -> list.isEmpty() ? new ArrayList<>() : list);
    }
}
