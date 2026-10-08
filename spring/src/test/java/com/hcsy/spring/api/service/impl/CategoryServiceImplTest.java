package com.hcsy.spring.api.service.impl;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyIterable;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.time.LocalDateTime;
import java.util.Arrays;
import java.util.List;
import java.util.Set;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.transaction.reactive.TransactionalOperator;

import com.hcsy.spring.api.repository.CategoryRepository;
import com.hcsy.spring.api.repository.SubCategoryRepository;
import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.exceptions.BusinessException;
import com.hcsy.spring.common.utils.CacheUtil;
import com.hcsy.spring.entity.dto.CategoryCreateDTO;
import com.hcsy.spring.entity.dto.CategoryUpdateDTO;
import com.hcsy.spring.entity.dto.SubCategoryUpdateDTO;
import com.hcsy.spring.entity.po.Category;
import com.hcsy.spring.entity.po.SubCategory;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

@ExtendWith(MockitoExtension.class)
class CategoryServiceImplTest {

    private static final Long CATEGORY_ID = 11L;
    private static final Long SUB_CATEGORY_ID = 22L;

    @Mock
    private CategoryRepository categoryRepository;
    @Mock
    private SubCategoryRepository subCategoryRepository;
    @Mock
    private CacheUtil cacheUtil;
    @Mock
    private TransactionalOperator transactionalOperator;

    private CategoryServiceImpl categoryService;

    @BeforeEach
    void setUp() {
        categoryService = new CategoryServiceImpl(categoryRepository, subCategoryRepository, cacheUtil,
            transactionalOperator);
    }

    @Test
    @DisplayName("新增分类返回保存后的主键并失效分类缓存")
    void addCategoryReturnsSavedIdAndEvictsCache() {
        CategoryCreateDTO dto = new CategoryCreateDTO();
        dto.setName("技术");
        stubTransactional();
        when(categoryRepository.save(any(Category.class))).thenAnswer(invocation -> {
            Category saved = invocation.getArgument(0);
            saved.setId(CATEGORY_ID);
            return Mono.just(saved);
        });
        stubCategoryCacheEviction();

        StepVerifier.create(categoryService.addCategory(dto))
            .expectNext(CATEGORY_ID)
            .verifyComplete();

        verify(cacheUtil).evictAll(anyString(), any(CacheUtil.CacheOptions[].class));
    }

    @Test
    @DisplayName("更新不存在的分类返回未找到且不落库")
    void updateCategoryRejectsMissingCategory() {
        CategoryUpdateDTO dto = new CategoryUpdateDTO();
        dto.setId(CATEGORY_ID);
        dto.setName("新技术");
        when(categoryRepository.findById(CATEGORY_ID)).thenReturn(Mono.empty());
        stubTransactional();
        stubCategoryCacheEviction();

        StepVerifier.create(categoryService.updateCategory(dto))
            .expectErrorMatches(error -> isBusinessError(error, HttpCode.NOT_FOUND,
                Messages.UNDEFINED_CATEGORY))
            .verify();

        verify(categoryRepository, never()).save(any(Category.class));
    }

    @Test
    @DisplayName("删除不存在的分类返回未找到且不级联删除子分类")
    void deleteCategoryRejectsMissingCategory() {
        when(categoryRepository.findById(CATEGORY_ID)).thenReturn(Mono.empty());
        stubTransactional();
        stubCategoryCacheEviction();

        StepVerifier.create(categoryService.deleteCategory(CATEGORY_ID))
            .expectErrorMatches(error -> isBusinessError(error, HttpCode.NOT_FOUND,
                Messages.UNDEFINED_CATEGORY))
            .verify();

        verify(subCategoryRepository, never()).deleteByCategoryId(any());
    }

    @Test
    @DisplayName("删除分类时先清理子分类再删除分类并失效缓存")
    void deleteCategoryRemovesSubCategoriesFirst() {
        when(categoryRepository.findById(CATEGORY_ID)).thenReturn(Mono.just(category()));
        when(subCategoryRepository.deleteByCategoryId(CATEGORY_ID)).thenReturn(Mono.empty());
        when(categoryRepository.deleteById(CATEGORY_ID)).thenReturn(Mono.empty());
        stubTransactional();
        stubCategoryCacheEviction();

        StepVerifier.create(categoryService.deleteCategory(CATEGORY_ID)).verifyComplete();

        verify(subCategoryRepository).deleteByCategoryId(CATEGORY_ID);
        verify(categoryRepository).deleteById(CATEGORY_ID);
    }

    @Test
    @DisplayName("批量删除分类时空入参或全空 ID 直接完成且不开启事务")
    void deleteCategoriesSkipsEmptyInput() {
        StepVerifier.create(categoryService.deleteCategories(List.of())).verifyComplete();
        StepVerifier.create(categoryService.deleteCategories(Arrays.asList((Long) null))).verifyComplete();

        verify(transactionalOperator, never()).transactional(any(Mono.class));
        verify(categoryRepository, never()).deleteById(anyLong());
    }

    @Test
    @DisplayName("批量删除分类时存在不存在的分类则整体拒绝")
    void deleteCategoriesRejectsPartiallyMissingCategories() {
        when(categoryRepository.findAllById(List.of(1L, 2L))).thenReturn(Flux.just(category()));
        stubTransactional();
        stubCategoryCacheEviction();

        StepVerifier.create(categoryService.deleteCategories(List.of(1L, 2L)))
            .expectErrorMatches(error -> isBusinessError(error, HttpCode.NOT_FOUND,
                Messages.UNDEFINED_CATEGORIES))
            .verify();

        verify(categoryRepository, never()).deleteById(anyLong());
    }

    @Test
    @DisplayName("更新不存在的子分类返回未找到")
    void updateSubCategoryRejectsMissingSubCategory() {
        SubCategoryUpdateDTO dto = new SubCategoryUpdateDTO();
        dto.setId(SUB_CATEGORY_ID);
        dto.setName("新子分类");
        dto.setCategoryId(CATEGORY_ID);
        when(subCategoryRepository.findById(SUB_CATEGORY_ID)).thenReturn(Mono.empty());
        stubTransactional();
        stubCategoryCacheEviction();

        StepVerifier.create(categoryService.updateSubCategory(dto))
            .expectErrorMatches(error -> isBusinessError(error, HttpCode.NOT_FOUND,
                Messages.UNDEFINED_SUB_CATEGORY))
            .verify();

        verify(subCategoryRepository, never()).save(any(SubCategory.class));
    }

    @Test
    @DisplayName("批量删除子分类时空入参直接完成")
    void deleteSubCategoriesSkipsEmptyInput() {
        StepVerifier.create(categoryService.deleteSubCategories(List.of())).verifyComplete();

        verify(transactionalOperator, never()).transactional(any(Mono.class));
        verify(subCategoryRepository, never()).deleteAllById(anyIterable());
    }

    @Test
    @DisplayName("批量删除子分类时存在不存在的子分类则整体拒绝")
    void deleteSubCategoriesRejectsPartiallyMissingSubCategories() {
        when(subCategoryRepository.findAllById(List.of(1L, 2L))).thenReturn(Flux.just(subCategory()));
        when(subCategoryRepository.deleteAllById(List.of(1L, 2L))).thenReturn(Mono.empty());
        stubTransactional();
        stubCategoryCacheEviction();

        StepVerifier.create(categoryService.deleteSubCategories(List.of(1L, 2L)))
            .expectErrorMatches(error -> isBusinessError(error, HttpCode.NOT_FOUND,
                Messages.UNDEFINED_SUB_CATEGORIES))
            .verify();

        verify(subCategoryRepository).findAllById(List.of(1L, 2L));
    }

    @Test
    @DisplayName("子分类层级列表按父分类补齐分类名")
    void listSubCategoriesWithParentFillsCategoryName() {
        when(subCategoryRepository.findAll()).thenReturn(Flux.just(subCategory()));
        when(categoryRepository.findAllById(Set.of(CATEGORY_ID))).thenReturn(Flux.just(category()));

        StepVerifier.create(categoryService.listAllSubCategoriesWithParent())
            .assertNext(vo -> {
                assertThat(vo.getId()).isEqualTo(SUB_CATEGORY_ID);
                assertThat(vo.getName()).isEqualTo("后端");
                assertThat(vo.getCategoryName()).isEqualTo("技术");
            })
            .verifyComplete();
    }

    @Test
    @DisplayName("父分类缺失时子分类层级列表落到未分类文案")
    void listSubCategoriesWithParentFallsBackToUncategorized() {
        when(subCategoryRepository.findAll()).thenReturn(Flux.just(subCategory()));
        when(categoryRepository.findAllById(Set.of(CATEGORY_ID))).thenReturn(Flux.empty());

        StepVerifier.create(categoryService.listAllSubCategoriesWithParent())
            .assertNext(vo -> assertThat(vo.getCategoryName()).isEqualTo(Messages.UNCATEGORIZED))
            .verifyComplete();
    }

    @Test
    @DisplayName("全量同步分类时按全部数据转换，增量时按更新时间过滤")
    void getNeo4jSyncCategoriesSwitchesByTimestamp() {
        when(categoryRepository.findAll()).thenReturn(Flux.just(category()));

        StepVerifier.create(categoryService.getNeo4jSyncCategories("  "))
            .assertNext(list -> {
                assertThat(list).hasSize(1);
                assertThat(list.get(0).getId()).isEqualTo(CATEGORY_ID);
            })
            .verifyComplete();

        when(categoryRepository.findByUpdateTimeAfter(LocalDateTime.parse("2026-01-01T00:00:00")))
            .thenReturn(Flux.empty());

        StepVerifier.create(categoryService.getNeo4jSyncCategories("2026-01-01T00:00:00"))
            .assertNext(list -> assertThat(list).isEmpty())
            .verifyComplete();
    }

    private void stubTransactional() {
        when(transactionalOperator.transactional(any(Mono.class)))
            .thenAnswer(invocation -> invocation.getArgument(0));
    }

    private void stubCategoryCacheEviction() {
        when(cacheUtil.evictAll(anyString(), any(CacheUtil.CacheOptions[].class))).thenReturn(Mono.empty());
    }

    private Category category() {
        Category category = new Category();
        category.setId(CATEGORY_ID);
        category.setName("技术");
        return category;
    }

    private SubCategory subCategory() {
        SubCategory subCategory = new SubCategory();
        subCategory.setId(SUB_CATEGORY_ID);
        subCategory.setName("后端");
        subCategory.setCategoryId(CATEGORY_ID);
        return subCategory;
    }

    private boolean isBusinessError(Throwable error, int expectedStatus, String expectedMessage) {
        return error instanceof BusinessException businessException
            && businessException.getHttpStatus() == expectedStatus
            && expectedMessage.equals(businessException.getErrorMessage());
    }
}
