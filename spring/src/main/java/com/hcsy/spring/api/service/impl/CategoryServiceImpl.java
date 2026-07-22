package com.hcsy.spring.api.service.impl;

import java.util.Collection;
import java.util.List;

import org.springframework.stereotype.Service;
import org.springframework.transaction.reactive.TransactionalOperator;

import com.hcsy.spring.api.repository.CategoryRepository;
import com.hcsy.spring.api.repository.SubCategoryRepository;
import com.hcsy.spring.api.service.CategoryCacheService;
import com.hcsy.spring.api.service.CategoryService;
import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.exceptions.BusinessException;
import com.hcsy.spring.entity.dto.CategoryCreateDTO;
import com.hcsy.spring.entity.dto.CategoryUpdateDTO;
import com.hcsy.spring.entity.dto.PageDTO;
import com.hcsy.spring.entity.dto.SubCategoryCreateDTO;
import com.hcsy.spring.entity.dto.SubCategoryUpdateDTO;
import com.hcsy.spring.entity.po.Category;
import com.hcsy.spring.entity.po.SubCategory;
import com.hcsy.spring.entity.vo.CategoryVO;

import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

@Service
@RequiredArgsConstructor
public class CategoryServiceImpl implements CategoryService {

    private final CategoryRepository categoryRepository;
    private final SubCategoryRepository subCategoryRepository;
    private final CategoryCacheService categoryCacheService;
    private final TransactionalOperator transactionalOperator;

    @Override
    public Mono<Long> addCategory(CategoryCreateDTO dto) {
        Category category = new Category();
        category.setName(dto.getName());
        return transactionalOperator.transactional(categoryRepository.save(category))
                .flatMap(saved -> categoryCacheService.evictAllCategoryCaches().thenReturn(saved.getId()));
    }

    @SuppressWarnings("null")
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
                .then(categoryCacheService.evictAllCategoryCaches());
    }

    @SuppressWarnings("null")
    @Override
    public Mono<Void> deleteCategory(Long id) {
        Mono<Void> databaseOperation = categoryRepository.findById(id)
                .switchIfEmpty(Mono.error(notFound(Messages.UNDEFINED_CATEGORY)))
                .flatMap(category -> subCategoryRepository.deleteByCategoryId(id)
                        .then(categoryRepository.deleteById(id)));
        return transactionalOperator.transactional(databaseOperation)
                .then(categoryCacheService.evictAllCategoryCaches());
    }

    @SuppressWarnings("null")
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
                .then(categoryCacheService.evictAllCategoryCaches());
    }

    @Override
    public Mono<Long> addSubCategory(SubCategoryCreateDTO dto) {
        SubCategory subCategory = new SubCategory();
        subCategory.setName(dto.getName());
        subCategory.setCategoryId(dto.getCategoryId());
        return transactionalOperator.transactional(subCategoryRepository.save(subCategory))
                .flatMap(saved -> categoryCacheService.evictAllCategoryCaches().thenReturn(saved.getId()));
    }

    @SuppressWarnings("null")
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
                .then(categoryCacheService.evictAllCategoryCaches());
    }

    @SuppressWarnings("null")
    @Override
    public Mono<Void> deleteSubCategory(Long id) {
        Mono<Void> databaseOperation = subCategoryRepository.findById(id)
                .switchIfEmpty(Mono.error(notFound(Messages.UNDEFINED_SUB_CATEGORY)))
                .flatMap(subCategoryRepository::delete);
        return transactionalOperator.transactional(databaseOperation)
                .then(categoryCacheService.evictAllCategoryCaches());
    }

    @SuppressWarnings("null")
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
                .then(categoryCacheService.evictAllCategoryCaches());
    }

    @Override
    public Mono<CategoryVO> getCategoryById(Long id) {
        return categoryCacheService.getCategoryById(id);
    }

    @Override
    public Mono<PageDTO<CategoryVO>> pageCategory(long page, long size) {
        return categoryCacheService.cachedPageCategory(page, size);
    }

    @SuppressWarnings("null")
    @Override
    public Flux<Category> listByIds(Collection<Long> ids) {
        return categoryRepository.findAllById(ids);
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
}
