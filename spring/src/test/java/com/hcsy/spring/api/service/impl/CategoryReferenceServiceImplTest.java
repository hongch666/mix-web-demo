package com.hcsy.spring.api.service.impl;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.transaction.reactive.TransactionalOperator;

import com.hcsy.spring.api.repository.CategoryReferenceRepository;
import com.hcsy.spring.api.repository.SubCategoryRepository;
import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.exceptions.BusinessException;
import com.hcsy.spring.entity.dto.CategoryReferenceCreateDTO;
import com.hcsy.spring.entity.dto.CategoryReferenceUpdateDTO;
import com.hcsy.spring.entity.po.CategoryReference;
import com.hcsy.spring.entity.po.SubCategory;

import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

@ExtendWith(MockitoExtension.class)
class CategoryReferenceServiceImplTest {

    private static final Long SUB_CATEGORY_ID = 22L;
    private static final Long REFERENCE_ID = 33L;

    @Mock
    private CategoryReferenceRepository categoryReferenceRepository;
    @Mock
    private SubCategoryRepository subCategoryRepository;
    @Mock
    private TransactionalOperator transactionalOperator;

    private CategoryReferenceServiceImpl categoryReferenceService;

    @BeforeEach
    void setUp() {
        categoryReferenceService = new CategoryReferenceServiceImpl(categoryReferenceRepository,
            subCategoryRepository, transactionalOperator);
    }

    @Test
    @DisplayName("PDF 类型未提供链接时返回不可处理错误且不开启事务")
    void addRejectsPdfWithoutContent() {
        StepVerifier.create(categoryReferenceService.addCategoryReference(createDTO("pdf", null, null)))
            .expectErrorMatches(error -> isBusinessError(error, HttpCode.UNPROCESSABLE_ENTITY,
                Messages.PDF_EMPTY))
            .verify();

        verify(transactionalOperator, never()).transactional(any(Mono.class));
    }

    @Test
    @DisplayName("PDF 类型链接未以 .pdf 结尾时返回不可处理错误")
    void addRejectsPdfWithWrongSuffix() {
        StepVerifier.create(categoryReferenceService.addCategoryReference(
            createDTO("pdf", null, "https://example.com/doc.txt")))
            .expectErrorMatches(error -> isBusinessError(error, HttpCode.UNPROCESSABLE_ENTITY,
                Messages.PDF_TAIL))
            .verify();

        verify(transactionalOperator, never()).transactional(any(Mono.class));
    }

    @Test
    @DisplayName("link 类型未提供链接时返回不可处理错误")
    void addRejectsLinkWithoutContent() {
        StepVerifier.create(categoryReferenceService.addCategoryReference(createDTO("link", "", null)))
            .expectErrorMatches(error -> isBusinessError(error, HttpCode.UNPROCESSABLE_ENTITY,
                Messages.LINK_EMPTY))
            .verify();

        verify(transactionalOperator, never()).transactional(any(Mono.class));
    }

    @Test
    @DisplayName("新增参考文本时子分类不存在返回未找到")
    void addRejectsMissingSubCategory() {
        when(subCategoryRepository.findById(SUB_CATEGORY_ID)).thenReturn(Mono.empty());
        stubTransactional();

        StepVerifier.create(categoryReferenceService.addCategoryReference(
            createDTO("link", "https://example.com", null)))
            .expectErrorMatches(error -> isBusinessError(error, HttpCode.NOT_FOUND,
                Messages.UNDEFINED_SUB_CATEGORY))
            .verify();

        verify(categoryReferenceRepository, never()).save(any(CategoryReference.class));
    }

    @Test
    @DisplayName("新增参考文本成功时落库并返回主键")
    void addPersistsNewReferenceWhenAbsent() {
        when(subCategoryRepository.findById(SUB_CATEGORY_ID)).thenReturn(Mono.just(new SubCategory()));
        when(categoryReferenceRepository.findBySubCategoryId(SUB_CATEGORY_ID)).thenReturn(Mono.empty());
        stubTransactional();
        when(categoryReferenceRepository.save(any(CategoryReference.class))).thenAnswer(invocation -> {
            CategoryReference saved = invocation.getArgument(0);
            saved.setId(REFERENCE_ID);
            return Mono.just(saved);
        });

        StepVerifier.create(categoryReferenceService.addCategoryReference(
            createDTO("link", "https://example.com", null)))
            .expectNext(REFERENCE_ID)
            .verifyComplete();

        ArgumentCaptor<CategoryReference> captor = ArgumentCaptor.forClass(CategoryReference.class);
        verify(categoryReferenceRepository).save(captor.capture());
        assertThat(captor.getValue().getSubCategoryId()).isEqualTo(SUB_CATEGORY_ID);
        assertThat(captor.getValue().getType()).isEqualTo("link");
        assertThat(captor.getValue().getLink()).isEqualTo("https://example.com");
        assertThat(captor.getValue().getPdf()).isNull();
    }

    @Test
    @DisplayName("新增参考文本时子分类已存在参考文本返回冲突")
    void addRejectsExistingReference() {
        when(subCategoryRepository.findById(SUB_CATEGORY_ID)).thenReturn(Mono.just(new SubCategory()));
        when(categoryReferenceRepository.findBySubCategoryId(SUB_CATEGORY_ID))
            .thenReturn(Mono.just(reference("link", "https://old.example.com", null)));
        stubTransactional();

        StepVerifier.create(categoryReferenceService.addCategoryReference(
            createDTO("link", "https://example.com", null)))
            .expectErrorMatches(error -> isBusinessError(error, HttpCode.CONFLICT, Messages.REFERENCE_EXIST))
            .verify();

        verify(categoryReferenceRepository, never()).save(any(CategoryReference.class));
    }

    @Test
    @DisplayName("更新参考文本时子分类不存在返回未找到")
    void updateRejectsMissingSubCategory() {
        when(subCategoryRepository.findById(SUB_CATEGORY_ID)).thenReturn(Mono.empty());
        when(categoryReferenceRepository.findBySubCategoryId(SUB_CATEGORY_ID))
            .thenReturn(Mono.just(reference("link", "https://old.example.com", null)));
        stubTransactional();

        StepVerifier.create(categoryReferenceService.updateCategoryReference(
            updateDTO("link", "https://example.com", null)))
            .expectErrorMatches(error -> isBusinessError(error, HttpCode.NOT_FOUND,
                Messages.UNDEFINED_SUB_CATEGORY))
            .verify();

        verify(categoryReferenceRepository, never()).save(any(CategoryReference.class));
    }

    @Test
    @DisplayName("更新参考文本时不存在记录返回未找到")
    void updateRejectsMissingReference() {
        when(subCategoryRepository.findById(SUB_CATEGORY_ID)).thenReturn(Mono.just(new SubCategory()));
        when(categoryReferenceRepository.findBySubCategoryId(SUB_CATEGORY_ID)).thenReturn(Mono.empty());
        stubTransactional();

        StepVerifier.create(categoryReferenceService.updateCategoryReference(
            updateDTO("link", "https://example.com", null)))
            .expectErrorMatches(error -> isBusinessError(error, HttpCode.NOT_FOUND,
                Messages.REFERENCE_NOT_EXIST))
            .verify();

        verify(categoryReferenceRepository, never()).save(any(CategoryReference.class));
    }

    @Test
    @DisplayName("切换为 PDF 类型时清空原有链接")
    void updateSwitchesContentByType() {
        CategoryReference existing = reference("link", "https://old.example.com", null);
        existing.setId(REFERENCE_ID);
        when(subCategoryRepository.findById(SUB_CATEGORY_ID)).thenReturn(Mono.just(new SubCategory()));
        when(categoryReferenceRepository.findBySubCategoryId(SUB_CATEGORY_ID)).thenReturn(Mono.just(existing));
        stubTransactional();
        when(categoryReferenceRepository.save(any(CategoryReference.class)))
            .thenAnswer(invocation -> Mono.just(invocation.getArgument(0)));

        StepVerifier.create(categoryReferenceService.updateCategoryReference(
            updateDTO("pdf", null, "https://example.com/doc.pdf")))
            .verifyComplete();

        assertThat(existing.getType()).isEqualTo("pdf");
        assertThat(existing.getPdf()).isEqualTo("https://example.com/doc.pdf");
        assertThat(existing.getLink()).isNull();
    }

    @Test
    @DisplayName("删除参考文本时不存在记录返回未找到")
    void deleteRejectsMissingReference() {
        when(categoryReferenceRepository.findBySubCategoryId(SUB_CATEGORY_ID)).thenReturn(Mono.empty());
        stubTransactional();

        StepVerifier.create(categoryReferenceService.deleteCategoryReference(SUB_CATEGORY_ID))
            .expectErrorMatches(error -> isBusinessError(error, HttpCode.NOT_FOUND,
                Messages.REFERENCE_NOT_EXIST))
            .verify();

        verify(categoryReferenceRepository, never()).delete(any(CategoryReference.class));
    }

    @Test
    @DisplayName("删除存在的参考文本时执行删除")
    void deleteRemovesExistingReference() {
        CategoryReference existing = reference("link", "https://example.com", null);
        when(categoryReferenceRepository.findBySubCategoryId(SUB_CATEGORY_ID)).thenReturn(Mono.just(existing));
        when(categoryReferenceRepository.delete(existing)).thenReturn(Mono.empty());
        stubTransactional();

        StepVerifier.create(categoryReferenceService.deleteCategoryReference(SUB_CATEGORY_ID)).verifyComplete();

        verify(categoryReferenceRepository).delete(existing);
    }

    @Test
    @DisplayName("查询参考文本时按类型只回填对应字段")
    void getReferenceFillsOnlyMatchingField() {
        CategoryReference existing = reference("link", "https://example.com", "https://example.com/doc.pdf");
        existing.setSubCategoryId(SUB_CATEGORY_ID);
        when(categoryReferenceRepository.findBySubCategoryId(SUB_CATEGORY_ID)).thenReturn(Mono.just(existing));

        StepVerifier.create(categoryReferenceService.getCategoryReferenceBySubCategoryId(SUB_CATEGORY_ID))
            .assertNext(vo -> {
                assertThat(vo.getType()).isEqualTo("link");
                assertThat(vo.getSubCategoryId()).isEqualTo(SUB_CATEGORY_ID);
                assertThat(vo.getLink()).isEqualTo("https://example.com");
                assertThat(vo.getPdf()).isNull();
            })
            .verifyComplete();
    }

    @Test
    @DisplayName("查询不存在的参考文本时返回空结果")
    void getReferenceReturnsEmptyWhenAbsent() {
        when(categoryReferenceRepository.findBySubCategoryId(SUB_CATEGORY_ID)).thenReturn(Mono.empty());

        StepVerifier.create(categoryReferenceService.getCategoryReferenceBySubCategoryId(SUB_CATEGORY_ID))
            .verifyComplete();
    }

    private void stubTransactional() {
        when(transactionalOperator.transactional(any(Mono.class)))
            .thenAnswer(invocation -> invocation.getArgument(0));
    }

    private CategoryReferenceCreateDTO createDTO(String type, String link, String pdf) {
        CategoryReferenceCreateDTO dto = new CategoryReferenceCreateDTO();
        dto.setSubCategoryId(SUB_CATEGORY_ID);
        dto.setType(type);
        dto.setLink(link);
        dto.setPdf(pdf);
        return dto;
    }

    private CategoryReferenceUpdateDTO updateDTO(String type, String link, String pdf) {
        CategoryReferenceUpdateDTO dto = new CategoryReferenceUpdateDTO();
        dto.setSubCategoryId(SUB_CATEGORY_ID);
        dto.setType(type);
        dto.setLink(link);
        dto.setPdf(pdf);
        return dto;
    }

    private CategoryReference reference(String type, String link, String pdf) {
        CategoryReference reference = new CategoryReference();
        reference.setType(type);
        reference.setLink(link);
        reference.setPdf(pdf);
        return reference;
    }

    private boolean isBusinessError(Throwable error, int expectedStatus, String expectedMessage) {
        return error instanceof BusinessException businessException
            && businessException.getHttpStatus() == expectedStatus
            && expectedMessage.equals(businessException.getErrorMessage());
    }
}
