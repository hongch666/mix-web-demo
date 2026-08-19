package com.hcsy.spring.api.controller;

import java.util.Arrays;
import java.util.List;
import java.util.Map;

import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.hcsy.spring.api.service.CategoryReferenceService;
import com.hcsy.spring.api.service.CategoryService;
import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.core.annotation.ApiLog;
import com.hcsy.spring.core.annotation.Neo4jSync;
import com.hcsy.spring.core.annotation.RequireInternalToken;
import com.hcsy.spring.core.annotation.RequirePermission;
import com.hcsy.spring.entity.dto.BatchIdsDTO;
import com.hcsy.spring.entity.dto.CategoryCreateDTO;
import com.hcsy.spring.entity.dto.CategoryUpdateDTO;
import com.hcsy.spring.entity.dto.SubCategoryCreateDTO;
import com.hcsy.spring.entity.dto.SubCategoryUpdateDTO;
import com.hcsy.spring.entity.vo.CategoryVO;
import com.hcsy.spring.entity.vo.SubCategoryVO;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;

@RestController
@RequestMapping("/category")
@RequiredArgsConstructor
@Tag(name = "分类模块", description = "文章分类管理相关API，包括分类增删改查、子分类管理、层级查询等")
public class CategoryController {

    private final CategoryService categoryService;
    private final CategoryReferenceService categoryReferenceService;

    @Operation(summary = "新增分类")
    @PostMapping()
    @RequirePermission(roles = { "admin" }, businessType = "category", paramSource = "body", paramNames = { "id" })
    @Neo4jSync(description = "新增分类后同步 Neo4j")
    @ApiLog("新增分类")
    public Mono<Result<Void>> addCategory(@Validated @RequestBody CategoryCreateDTO dto) {
        return categoryService.addCategory(dto).thenReturn(Result.<Void>success());
    }

    @Operation(summary = "修改分类")
    @PutMapping()
    @RequirePermission(roles = { "admin" }, businessType = "category", paramSource = "body", paramNames = { "id" })
    @Neo4jSync(description = "修改分类后同步 Neo4j")
    @ApiLog("修改分类")
    public Mono<Result<Void>> updateCategory(@Validated @RequestBody CategoryUpdateDTO dto) {
        return categoryService.updateCategory(dto).thenReturn(Result.<Void>success());
    }

    @Operation(summary = "删除分类（级联删除子分类）")
    @DeleteMapping("/{id}")
    @RequirePermission(roles = { "admin" }, businessType = "category", paramSource = "path_single", paramNames = {
        "id" })
    @Neo4jSync(description = "删除分类后同步 Neo4j")
    @ApiLog("删除分类")
    public Mono<Result<Void>> deleteCategory(@PathVariable Long id) {
        return categoryService.deleteCategory(id).thenReturn(Result.<Void>success());
    }

    @Operation(summary = "批量删除分类（级联删除子分类）")
    @DeleteMapping("/batch/{ids}")
    @RequirePermission(roles = { "admin" }, businessType = "category", paramSource = "path_single", paramNames = {
        "ids" })
    @Neo4jSync(description = "批量删除分类后同步 Neo4j")
    @ApiLog("批量删除分类")
    public Mono<Result<Void>> deleteCategories(@PathVariable String ids) {
        List<Long> idList = Arrays.stream(ids.split(","))
            .map(String::trim)
            .filter(s -> !s.isEmpty())
            .map(Long::valueOf)
            .toList();
        return categoryService.deleteCategories(idList).thenReturn(Result.<Void>success());
    }

    @Operation(summary = "新增子分类")
    @PostMapping("/sub")
    @RequirePermission(roles = { "admin" }, businessType = "subcategory", paramSource = "body", paramNames = { "id" })
    @Neo4jSync(description = "新增子分类后同步 Neo4j")
    @ApiLog("新增子分类")
    public Mono<Result<Void>> addSubCategory(@Validated @RequestBody SubCategoryCreateDTO dto) {
        return categoryService.addSubCategory(dto).thenReturn(Result.<Void>success());
    }

    @Operation(summary = "修改子分类")
    @PutMapping("/sub")
    @RequirePermission(roles = { "admin" }, businessType = "subcategory", paramSource = "body", paramNames = { "id" })
    @Neo4jSync(description = "修改子分类后同步 Neo4j")
    @ApiLog("修改子分类")
    public Mono<Result<Void>> updateSubCategory(@Validated @RequestBody SubCategoryUpdateDTO dto) {
        return categoryService.updateSubCategory(dto).thenReturn(Result.<Void>success());
    }

    @Operation(summary = "删除子分类")
    @DeleteMapping("/sub/{id}")
    @RequirePermission(roles = { "admin" }, businessType = "subcategory", paramSource = "path_single", paramNames = {
        "id" })
    @Neo4jSync(description = "删除子分类后同步 Neo4j")
    @ApiLog("删除子分类")
    public Mono<Result<Void>> deleteSubCategory(@PathVariable Long id) {
        return categoryService.deleteSubCategory(id).thenReturn(Result.<Void>success());
    }

    @Operation(summary = "批量删除子分类")
    @DeleteMapping("/sub/batch/{ids}")
    @RequirePermission(roles = { "admin" }, businessType = "subcategory", paramSource = "path_single", paramNames = {
        "ids" })
    @Neo4jSync(description = "批量删除子分类后同步 Neo4j")
    @ApiLog("批量删除子分类")
    public Mono<Result<Void>> deleteSubCategories(@PathVariable String ids) {
        List<Long> idList = Arrays.stream(ids.split(","))
            .map(String::trim)
            .filter(s -> !s.isEmpty())
            .map(Long::valueOf)
            .toList();
        return categoryService.deleteSubCategories(idList).thenReturn(Result.<Void>success());
    }

    @Operation(summary = "分页查询分类（含子分类信息）")
    @GetMapping("/list")
    @ApiLog("分页查询分类")
    public Mono<Result<Map<String, Object>>> pageCategory(@RequestParam(defaultValue = "1") int page,
        @RequestParam(defaultValue = "10") int size) {
        return categoryService.pageCategory(page, size)
            .map(result -> Result.success(Map.of(
                "list", result.getRecords(),
                "total", result.getTotal())));
    }

    @Operation(summary = "根据ID查询分类（含子分类信息）")
    @GetMapping("/{id}")
    @ApiLog("根据ID查询分类")
    public Mono<Result<CategoryVO>> getCategoryById(@PathVariable Long id) {
        return categoryService.getCategoryById(id)
            .map(Result::success)
            .defaultIfEmpty(Result.<CategoryVO>error(HttpCode.NOT_FOUND, Messages.UNDEFINED_CATEGORY));
    }

    @PostMapping("/batch")
    @Operation(summary = "批量查询分类（内部）", description = "根据ID列表批量查询分类，供内部服务远程调用")
    @RequireInternalToken
    @ApiLog("内部批量查询分类")
    public Mono<Result<List<CategoryVO>>> getCategoryByIds(@Valid @RequestBody BatchIdsDTO dto) {
        return categoryService.listByIds(dto.getIds())
            .map(category -> {
                CategoryVO vo = new CategoryVO();
                org.springframework.beans.BeanUtils.copyProperties(category, vo);
                return vo;
            })
            .collectList()
            .map(Result::success);
    }

    @PostMapping("/sub/batch")
    @Operation(summary = "批量查询子分类（内部）", description = "根据ID列表批量查询子分类，供内部服务远程调用")
    @RequireInternalToken
    @ApiLog("内部批量查询子分类")
    public Mono<Result<List<SubCategoryVO>>> getSubCategoryByIds(@Valid @RequestBody BatchIdsDTO dto) {
        return categoryService.listSubCategoriesByIds(dto.getIds())
            .map(sub -> {
                SubCategoryVO vo = new SubCategoryVO();
                org.springframework.beans.BeanUtils.copyProperties(sub, vo);
                return vo;
            })
            .collectList()
            .map(Result::success);
    }

    // ==================== 内部接口 ====================

    @GetMapping("/internal/all")
    @Operation(summary = "获取所有分类（内部）", description = "获取所有分类列表，供内部服务远程调用")
    @RequireInternalToken
    @ApiLog("内部获取所有分类")
    public Mono<Result<List<CategoryVO>>> getAllCategories() {
        return categoryService.listAllCategories()
            .map(category -> {
                CategoryVO vo = new CategoryVO();
                org.springframework.beans.BeanUtils.copyProperties(category, vo);
                return vo;
            })
            .collectList()
            .map(Result::success);
    }

    @GetMapping("/internal/sub/with-parent")
    @Operation(summary = "获取子分类及其父分类信息（内部）", description = "获取所有子分类及对应的父分类名称，供内部服务远程调用")
    @RequireInternalToken
    @ApiLog("内部获取子分类及父分类信息")
    public Mono<Result<List<Map<String, Object>>>> getSubcategoriesWithParent() {
        return categoryService.listAllSubCategoriesWithParent()
            .collectList()
            .map(Result::success);
    }

    @GetMapping("/internal/reference/sub/{sub_category_id}")
    @Operation(summary = "获取子分类权威参考文本（内部）", description = "根据子分类ID获取权威参考文本，供内部服务远程调用")
    @RequireInternalToken
    @ApiLog("内部获取子分类权威参考文本")
    public Mono<Result<com.hcsy.spring.entity.vo.CategoryReferenceVO>> getCategoryReferenceBySubCategoryId(
        @PathVariable("sub_category_id") Long subCategoryId) {
        return categoryReferenceService.getCategoryReferenceBySubCategoryId(subCategoryId)
            .map(Result::success)
            .defaultIfEmpty(Result.<com.hcsy.spring.entity.vo.CategoryReferenceVO>success(null));
    }
}
