package com.hcsy.spring.application.service.impl;

import org.springframework.stereotype.Service;
import org.springframework.transaction.reactive.TransactionalOperator;

import com.hcsy.spring.application.service.CategoryReferenceService;
import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.exceptions.BusinessException;
import com.hcsy.spring.entity.dto.CategoryReferenceCreateDTO;
import com.hcsy.spring.entity.dto.CategoryReferenceUpdateDTO;
import com.hcsy.spring.entity.po.CategoryReference;
import com.hcsy.spring.entity.vo.CategoryReferenceVO;
import com.hcsy.spring.infra.repository.CategoryReferenceRepository;
import com.hcsy.spring.infra.repository.SubCategoryRepository;

import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;

/**
 * CategoryReferenceService 的实现，校验参考资料类型与内容后在事务中维护子分类参考资料，并按类型清除视图中的无关字段
 */
@Service
@RequiredArgsConstructor
public class CategoryReferenceServiceImpl implements CategoryReferenceService {

    private final CategoryReferenceRepository categoryReferenceRepository;
    private final SubCategoryRepository subCategoryRepository;
    private final TransactionalOperator transactionalOperator;

    /**
     * 实现为子分类新增参考资料，校验类型内容且已存在时抛冲突异常
     */
    @Override
    public Mono<Long> addCategoryReference(CategoryReferenceCreateDTO dto) {
        BusinessException validationError = validateContent(dto.getType(), dto.getLink(), dto.getPdf());
        if (validationError != null) {
            return Mono.error(validationError);
        }

        // 子分类必须存在，参考文本不存在时才创建；defer 保证 save 只在真正需要时订阅
        Mono<CategoryReference> operation = subCategoryRepository.findById(dto.getSubCategoryId())
            .switchIfEmpty(Mono.error(notFound(Messages.UNDEFINED_SUB_CATEGORY)))
            .flatMap(subCategory -> categoryReferenceRepository.findBySubCategoryId(dto.getSubCategoryId())
                .flatMap(existing -> Mono.<CategoryReference>error(conflict(Messages.REFERENCE_EXIST)))
                .switchIfEmpty(Mono.defer(() -> categoryReferenceRepository.save(toEntity(dto)))));

        return transactionalOperator.transactional(operation).map(CategoryReference::getId);
    }

    /**
     * 实现更新子分类参考资料，校验子分类与参考均存在
     */
    @Override
    public Mono<Void> updateCategoryReference(CategoryReferenceUpdateDTO dto) {
        BusinessException validationError = validateContent(dto.getType(), dto.getLink(), dto.getPdf());
        if (validationError != null) {
            return Mono.error(validationError);
        }

        Mono<Void> operation = Mono.zip(
            subCategoryRepository.findById(dto.getSubCategoryId())
                .switchIfEmpty(Mono.error(notFound(Messages.UNDEFINED_SUB_CATEGORY))),
            categoryReferenceRepository.findBySubCategoryId(dto.getSubCategoryId())
                .switchIfEmpty(Mono.error(notFound(Messages.REFERENCE_NOT_EXIST))))
            .flatMap(result -> {
                CategoryReference reference = result.getT2();
                applyContent(reference, dto.getType(), dto.getLink(), dto.getPdf());
                return categoryReferenceRepository.save(reference);
            })
            .then();
        return transactionalOperator.transactional(operation);
    }

    /**
     * 实现删除子分类参考资料，不存在时抛404异常
     */
    @Override
    public Mono<Void> deleteCategoryReference(Long subCategoryId) {
        Mono<Void> operation = categoryReferenceRepository.findBySubCategoryId(subCategoryId)
            .switchIfEmpty(Mono.error(notFound(Messages.REFERENCE_NOT_EXIST)))
            .flatMap(categoryReferenceRepository::delete);
        return transactionalOperator.transactional(operation);
    }

    /**
     * 实现按子分类ID查询参考资料并转为视图对象
     */
    @Override
    public Mono<CategoryReferenceVO> getCategoryReferenceBySubCategoryId(Long subCategoryId) {
        return categoryReferenceRepository.findBySubCategoryId(subCategoryId).map(this::toVO);
    }

    /**
     * 将创建DTO转换为参考资料实体
     */
    private CategoryReference toEntity(CategoryReferenceCreateDTO dto) {
        CategoryReference reference = new CategoryReference();
        reference.setSubCategoryId(dto.getSubCategoryId());
        applyContent(reference, dto.getType(), dto.getLink(), dto.getPdf());
        return reference;
    }

    /**
     * 按类型设置参考资料内容，仅link类型存链接、pdf类型存文件
     */
    private void applyContent(CategoryReference reference, String type, String link, String pdf) {
        reference.setType(type);
        reference.setLink("link".equals(type) ? link : null);
        reference.setPdf("pdf".equals(type) ? pdf : null);
    }

    /**
     * 将参考资料实体转为视图对象，按类型清除无关字段
     */
    private CategoryReferenceVO toVO(CategoryReference reference) {
        CategoryReferenceVO vo = new CategoryReferenceVO();
        vo.setId(reference.getId());
        vo.setSubCategoryId(reference.getSubCategoryId());
        vo.setType(reference.getType());
        vo.setLink("link".equals(reference.getType()) ? reference.getLink() : null);
        vo.setPdf("pdf".equals(reference.getType()) ? reference.getPdf() : null);
        return vo;
    }

    /**
     * 校验参考资料内容，pdf类型需以.pdf结尾、link类型不可为空
     */
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

    /**
     * 构造404资源不存在的业务异常
     */
    private BusinessException notFound(String message) {
        return BusinessException.builder().httpStatus(HttpCode.NOT_FOUND).errorMessage(message).build();
    }

    /**
     * 构造409资源冲突的业务异常
     */
    private BusinessException conflict(String message) {
        return BusinessException.builder().httpStatus(HttpCode.CONFLICT).errorMessage(message).build();
    }

    /**
     * 构造422不可处理实体的业务异常
     */
    private BusinessException unprocessable(String message) {
        return BusinessException.builder().httpStatus(HttpCode.UNPROCESSABLE_ENTITY).errorMessage(message).build();
    }
}
