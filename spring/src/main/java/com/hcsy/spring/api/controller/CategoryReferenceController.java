package com.hcsy.spring.api.controller;

import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.hcsy.spring.api.service.CategoryReferenceService;
import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.core.annotation.ApiLog;
import com.hcsy.spring.core.annotation.RequirePermission;
import com.hcsy.spring.entity.dto.CategoryReferenceCreateDTO;
import com.hcsy.spring.entity.dto.CategoryReferenceUpdateDTO;
import com.hcsy.spring.entity.vo.CategoryReferenceVO;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;

@RestController
@RequestMapping("/category/reference")
@RequiredArgsConstructor
@Tag(name = "权威参考文本模块", description = "分类权威参考文本相关API，包括参考文本增删改查等")
public class CategoryReferenceController {

    private final CategoryReferenceService categoryReferenceService;

    @Operation(summary = "创建权威参考文本")
    @PostMapping()
    @RequirePermission(
        roles = { "admin" },
        businessType = "categoryReference",
        paramSource = "body",
        paramNames = { "id" }
    )
    @ApiLog("创建权威参考文本")
    public Mono<Result<Void>> addCategoryReference(@Validated @RequestBody CategoryReferenceCreateDTO dto) {
        return Mono.deferContextual(ctx -> {
            categoryReferenceService.addCategoryReference(dto);
            return Mono.just(Result.<Void>success());
        });
    }

    @Operation(summary = "修改权威参考文本")
    @PutMapping()
    @RequirePermission(
        roles = { "admin" },
        businessType = "categoryReference",
        paramSource = "body",
        paramNames = { "id" }
    )
    @ApiLog("修改权威参考文本")
    public Mono<Result<Void>> updateCategoryReference(@Validated @RequestBody CategoryReferenceUpdateDTO dto) {
        return Mono.deferContextual(ctx -> {
            categoryReferenceService.updateCategoryReference(dto);
            return Mono.just(Result.<Void>success());
        });
    }

    @Operation(summary = "删除权威参考文本")
    @DeleteMapping("/sub/{sub_category_id}")
    @RequirePermission(
        roles = { "admin" },
        businessType = "categoryReference",
        paramSource = "path_single",
        paramNames = { "id" }
    )
    @ApiLog("删除权威参考文本")
    public Mono<Result<Void>> deleteCategoryReference(@PathVariable("sub_category_id") Long subCategoryId) {
        return Mono.deferContextual(ctx -> {
            categoryReferenceService.deleteCategoryReference(subCategoryId);
            return Mono.just(Result.<Void>success());
        });
    }

    @Operation(summary = "根据子分类ID获取权威参考文本")
    @GetMapping("/sub/{sub_category_id}")
    @ApiLog("查询权威参考文本")
    public Mono<Result<CategoryReferenceVO>> getCategoryReferenceBySubCategoryId(@PathVariable("sub_category_id") Long subCategoryId) {
        return Mono.deferContextual(ctx -> {
            CategoryReferenceVO vo = categoryReferenceService.getCategoryReferenceBySubCategoryId(subCategoryId);
            if (vo == null) {
                return Mono.just(Result.<CategoryReferenceVO>success(null));
            }
            return Mono.just(Result.success(vo));
        });
    }
}
