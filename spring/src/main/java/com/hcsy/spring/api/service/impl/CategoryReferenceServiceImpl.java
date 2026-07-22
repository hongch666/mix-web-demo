package com.hcsy.spring.api.service.impl;

import org.springframework.stereotype.Service;
import org.springframework.transaction.reactive.TransactionalOperator;

import com.hcsy.spring.api.repository.CategoryReferenceRepository;
import com.hcsy.spring.api.repository.SubCategoryRepository;
import com.hcsy.spring.api.service.CategoryReferenceService;
import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.exceptions.BusinessException;
import com.hcsy.spring.entity.dto.CategoryReferenceCreateDTO;
import com.hcsy.spring.entity.dto.CategoryReferenceUpdateDTO;
import com.hcsy.spring.entity.po.CategoryReference;
import com.hcsy.spring.entity.vo.CategoryReferenceVO;

import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;

@Service
@RequiredArgsConstructor
public class CategoryReferenceServiceImpl implements CategoryReferenceService {

    private final CategoryReferenceRepository categoryReferenceRepository;
    private final SubCategoryRepository subCategoryRepository;
    private final TransactionalOperator transactionalOperator;

    @SuppressWarnings("null")
    @Override
    public Mono<Long> addCategoryReference(CategoryReferenceCreateDTO dto) {
        BusinessException validationError = validateContent(dto.getType(), dto.getLink(), dto.getPdf());
        if (validationError != null) {
            return Mono.error(validationError);
        }

        Mono<CategoryReference> operation = subCategoryRepository.findById(dto.getSubCategoryId())
                .switchIfEmpty(Mono.error(notFound(Messages.UNDEFINED_SUB_CATEGORY)))
                .then(categoryReferenceRepository.findBySubCategoryId(dto.getSubCategoryId())
                        .flatMap(existing -> Mono.<CategoryReference>error(conflict(Messages.REFERENCE_EXIST)))
                        .switchIfEmpty(Mono.defer(() -> categoryReferenceRepository.save(toEntity(dto)))));

        return transactionalOperator.transactional(operation).map(CategoryReference::getId);
    }

    @SuppressWarnings("null")
    @Override
    public Mono<Void> updateCategoryReference(CategoryReferenceUpdateDTO dto) {
        BusinessException validationError = validateContent(dto.getType(), dto.getLink(), dto.getPdf());
        if (validationError != null) {
            return Mono.error(validationError);
        }

        Mono<Void> operation = subCategoryRepository.findById(dto.getSubCategoryId())
                .switchIfEmpty(Mono.error(notFound(Messages.UNDEFINED_SUB_CATEGORY)))
                .then(categoryReferenceRepository.findBySubCategoryId(dto.getSubCategoryId())
                        .switchIfEmpty(Mono.error(conflict(Messages.REFERENCE_EXIST)))
                        .flatMap(reference -> {
                            applyContent(reference, dto.getType(), dto.getLink(), dto.getPdf());
                            return categoryReferenceRepository.save(reference);
                        }))
                .then();
        return transactionalOperator.transactional(operation);
    }

    @SuppressWarnings("null")
    @Override
    public Mono<Void> deleteCategoryReference(Long subCategoryId) {
        Mono<Void> operation = categoryReferenceRepository.findBySubCategoryId(subCategoryId)
                .switchIfEmpty(Mono.error(conflict(Messages.REFERENCE_EXIST)))
                .flatMap(categoryReferenceRepository::delete);
        return transactionalOperator.transactional(operation);
    }

    @Override
    public Mono<CategoryReferenceVO> getCategoryReferenceBySubCategoryId(Long subCategoryId) {
        return categoryReferenceRepository.findBySubCategoryId(subCategoryId).map(this::toVO);
    }

    private CategoryReference toEntity(CategoryReferenceCreateDTO dto) {
        CategoryReference reference = new CategoryReference();
        reference.setSubCategoryId(dto.getSubCategoryId());
        applyContent(reference, dto.getType(), dto.getLink(), dto.getPdf());
        return reference;
    }

    private void applyContent(CategoryReference reference, String type, String link, String pdf) {
        reference.setType(type);
        reference.setLink("link".equals(type) ? link : null);
        reference.setPdf("pdf".equals(type) ? pdf : null);
    }

    private CategoryReferenceVO toVO(CategoryReference reference) {
        CategoryReferenceVO vo = new CategoryReferenceVO();
        vo.setId(reference.getId());
        vo.setSubCategoryId(reference.getSubCategoryId());
        vo.setType(reference.getType());
        vo.setLink("link".equals(reference.getType()) ? reference.getLink() : null);
        vo.setPdf("pdf".equals(reference.getType()) ? reference.getPdf() : null);
        return vo;
    }

    private BusinessException validateContent(String type, String link, String pdf) {
        if ("pdf".equals(type)) {
            if (pdf == null || pdf.isEmpty()) {
                return unprocessable(Messages.PDF_EMPTY);
            }
            if (!pdf.toLowerCase().endsWith(".pdf")) {
                return unprocessable(Messages.PDF_TAIL);
            }
        }
        if ("link".equals(type) && (link == null || link.isEmpty())) {
            return unprocessable(Messages.LINK_EMPTY);
        }
        return null;
    }

    private BusinessException notFound(String message) {
        return BusinessException.builder().httpStatus(HttpCode.NOT_FOUND).errorMessage(message).build();
    }

    private BusinessException conflict(String message) {
        return BusinessException.builder().httpStatus(HttpCode.CONFLICT).errorMessage(message).build();
    }

    private BusinessException unprocessable(String message) {
        return BusinessException.builder().httpStatus(HttpCode.UNPROCESSABLE_ENTITY).errorMessage(message).build();
    }
}
