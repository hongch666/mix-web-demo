package com.hcsy.spring.api.service.impl;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.util.List;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import com.hcsy.spring.api.repository.SubCategoryRepository;
import com.hcsy.spring.entity.po.SubCategory;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

@ExtendWith(MockitoExtension.class)
class SubCategoryServiceImplTest {

    private static final Long SUB_CATEGORY_ID = 6L;
    private static final Long CATEGORY_ID = 2L;

    @Mock
    private SubCategoryRepository subCategoryRepository;

    private SubCategoryServiceImpl subCategoryService;

    @BeforeEach
    void setUp() {
        subCategoryService = new SubCategoryServiceImpl(subCategoryRepository);
    }

    @Test
    @DisplayName("按 ID 查询子分类直接透传仓库结果")
    void getByIdDelegatesToRepository() {
        when(subCategoryRepository.findById(SUB_CATEGORY_ID)).thenReturn(Mono.just(subCategory()));

        StepVerifier.create(subCategoryService.getById(SUB_CATEGORY_ID))
            .assertNext(result -> {
                assertThat(result.getId()).isEqualTo(SUB_CATEGORY_ID);
                assertThat(result.getCategoryId()).isEqualTo(CATEGORY_ID);
            })
            .verifyComplete();

        verify(subCategoryRepository).findById(SUB_CATEGORY_ID);
    }

    @Test
    @DisplayName("按 ID 集合查询子分类直接透传仓库结果")
    void listByIdsDelegatesToRepository() {
        when(subCategoryRepository.findAllById(List.of(SUB_CATEGORY_ID))).thenReturn(Flux.just(subCategory()));

        StepVerifier.create(subCategoryService.listByIds(List.of(SUB_CATEGORY_ID)))
            .assertNext(result -> assertThat(result.getName()).isEqualTo("后端"))
            .verifyComplete();

        verify(subCategoryRepository).findAllById(List.of(SUB_CATEGORY_ID));
    }

    private SubCategory subCategory() {
        SubCategory subCategory = new SubCategory();
        subCategory.setId(SUB_CATEGORY_ID);
        subCategory.setName("后端");
        subCategory.setCategoryId(CATEGORY_ID);
        return subCategory;
    }
}
