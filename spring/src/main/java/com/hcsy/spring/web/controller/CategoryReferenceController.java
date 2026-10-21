package com.hcsy.spring.web.controller;

import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.hcsy.spring.application.service.CategoryReferenceService;
import com.hcsy.spring.common.constants.BusinessType;
import com.hcsy.spring.common.constants.ParamSource;
import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.entity.dto.CategoryReferenceCreateDTO;
import com.hcsy.spring.entity.dto.CategoryReferenceUpdateDTO;
import com.hcsy.spring.entity.vo.CategoryReferenceVO;
import com.hcsy.spring.web.logging.annotation.ApiLog;
import com.hcsy.spring.web.security.annotation.RequirePermission;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;

/**
 * 权威参考文本控制器，聚合 /category/reference 下参考资料的创建、修改、删除与查询接口
 */
@RestController
@RequestMapping("/category/reference")
@RequiredArgsConstructor
@Tag(name = "权威参考文本模块", description = "分类权威参考文本相关API，包括参考文本增删改查等")
public class CategoryReferenceController {

    private final CategoryReferenceService categoryReferenceService;

    /**
     * POST /category/reference 接口，管理员在指定子分类下创建权威参考文本内容
     */
    @Operation(summary = "创建权威参考文本", description = "管理员在指定子分类下创建权威参考文本内容")
    @PostMapping()
    @RequirePermission(roles = { "admin" }, businessType = BusinessType.CATEGORY_REFERENCE,
        paramSource = ParamSource.BODY,
        paramName = "id")
    @ApiLog("创建权威参考文本")
    public Mono<Result<Void>> addCategoryReference(@Validated @RequestBody CategoryReferenceCreateDTO dto) {
        return categoryReferenceService.addCategoryReference(dto).thenReturn(Result.<Void>success());
    }

    /**
     * PUT /category/reference 接口，管理员修改指定子分类下的权威参考文本内容
     */
    @Operation(summary = "修改权威参考文本", description = "管理员修改指定子分类下的权威参考文本内容")
    @PutMapping()
    @RequirePermission(roles = { "admin" }, businessType = BusinessType.CATEGORY_REFERENCE,
        paramSource = ParamSource.BODY,
        paramName = "id")
    @ApiLog("修改权威参考文本")
    public Mono<Result<Void>> updateCategoryReference(@Validated @RequestBody CategoryReferenceUpdateDTO dto) {
        return categoryReferenceService.updateCategoryReference(dto).thenReturn(Result.<Void>success());
    }

    /**
     * DELETE /category/reference/sub/{sub_category_id} 接口，管理员删除指定子分类下的权威参考文本
     */
    @Operation(summary = "删除权威参考文本", description = "管理员删除指定子分类下的权威参考文本")
    @DeleteMapping("/sub/{sub_category_id}")
    @RequirePermission(roles = {
        "admin" }, businessType = BusinessType.CATEGORY_REFERENCE, paramSource = ParamSource.PATH_SINGLE,
        paramName = "id")
    @ApiLog("删除权威参考文本")
    public Mono<Result<Void>> deleteCategoryReference(@PathVariable("sub_category_id") Long subCategoryId) {
        return categoryReferenceService.deleteCategoryReference(subCategoryId).thenReturn(Result.<Void>success());
    }

    /**
     * GET /category/reference/sub/{sub_category_id} 接口，按子分类ID返回其权威参考文本，不存在时返回空数据
     */
    @Operation(summary = "根据子分类ID获取权威参考文本", description = "根据子分类ID查询其关联的权威参考文本，不存在时返回空数据")
    @GetMapping("/sub/{sub_category_id}")
    @ApiLog("查询权威参考文本")
    public Mono<Result<CategoryReferenceVO>> getCategoryReferenceBySubCategoryId(
        @PathVariable("sub_category_id") Long subCategoryId) {
        return categoryReferenceService.getCategoryReferenceBySubCategoryId(subCategoryId)
            .map(Result::success)
            .defaultIfEmpty(Result.<CategoryReferenceVO>success(null));
    }
}
