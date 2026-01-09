package com.hcsy.spring.api.controller;

import io.swagger.v3.oas.annotations.tags.Tag;
import io.swagger.v3.oas.annotations.Operation;
import lombok.RequiredArgsConstructor;
import com.hcsy.spring.api.service.CategoryReferenceService;
import com.hcsy.spring.common.annotation.ApiLog;
import com.hcsy.spring.common.annotation.RequirePermission;
import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.entity.dto.CategoryReferenceCreateDTO;
import com.hcsy.spring.entity.dto.CategoryReferenceUpdateDTO;
import com.hcsy.spring.entity.vo.CategoryReferenceVO;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/category/reference")
@RequiredArgsConstructor
@Tag(name = "权威参考文本模块", description = "分类权威参考文本相关接口")
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
    public Result addCategoryReference(@Validated @RequestBody CategoryReferenceCreateDTO dto) {
        categoryReferenceService.addCategoryReference(dto);
        return Result.success();
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
    public Result updateCategoryReference(@Validated @RequestBody CategoryReferenceUpdateDTO dto) {
        categoryReferenceService.updateCategoryReference(dto);
        return Result.success();
    }

    @Operation(summary = "删除权威参考文本")
    @DeleteMapping("/sub/{subCategoryId}")
    @RequirePermission(
        roles = { "admin" }, 
        businessType = "categoryReference", 
        paramSource = "path_single", 
        paramNames = { "id" }
    )
    @ApiLog("删除权威参考文本")
    public Result deleteCategoryReference(@PathVariable Long subCategoryId) {
        categoryReferenceService.deleteCategoryReference(subCategoryId);
        return Result.success();
    }

    @Operation(summary = "根据子分类ID获取权威参考文本")
    @GetMapping("/sub/{subCategoryId}")
    @ApiLog("查询权威参考文本")
    public Result getCategoryReferenceBySubCategoryId(@PathVariable Long subCategoryId) {
        CategoryReferenceVO vo = categoryReferenceService.getCategoryReferenceBySubCategoryId(subCategoryId);
        if (vo == null) {
            return Result.success(null);
        }
        return Result.success(vo);
    }
}
