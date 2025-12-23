package com.hcsy.spring.api.controller;

import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.hcsy.spring.api.service.CategoryService;
import com.hcsy.spring.common.annotation.ApiLog;
import com.hcsy.spring.common.annotation.RequirePermission;
import com.hcsy.spring.entity.dto.CategoryCreateDTO;
import com.hcsy.spring.entity.dto.CategoryUpdateDTO;
import com.hcsy.spring.entity.dto.SubCategoryCreateDTO;
import com.hcsy.spring.entity.dto.SubCategoryUpdateDTO;
import com.hcsy.spring.entity.po.Result;
import com.hcsy.spring.entity.vo.CategoryVO;

import io.swagger.v3.oas.annotations.Operation;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;
import java.util.Arrays;

@RestController
@RequestMapping("/category")
@RequiredArgsConstructor
@Tag(name = "分类模块", description = "分类相关接口")
public class CategoryController {

    private final CategoryService categoryService;

    @Operation(summary = "新增分类")
    @PostMapping()
    @RequirePermission(roles = { "admin" }, businessType = "category", paramSource = "body", paramNames = { "id" })
    @ApiLog("新增分类")
    public Result addCategory(@Validated @RequestBody CategoryCreateDTO dto) {
        categoryService.addCategory(dto);
        return Result.success();
    }

    @Operation(summary = "修改分类")
    @PutMapping()
    @RequirePermission(roles = { "admin" }, businessType = "category", paramSource = "body", paramNames = { "id" })
    @ApiLog("修改分类")
    public Result updateCategory(@Validated @RequestBody CategoryUpdateDTO dto) {
        categoryService.updateCategory(dto);
        return Result.success();
    }

    @Operation(summary = "删除分类（级联删除子分类）")
    @DeleteMapping("/{id}")
    @RequirePermission(roles = { "admin" }, businessType = "category", paramSource = "path_single", paramNames = {
            "id" })
    @ApiLog("删除分类")
    public Result deleteCategory(@PathVariable Long id) {
        categoryService.deleteCategory(id);
        return Result.success();
    }

    @Operation(summary = "批量删除分类（级联删除子分类）")
    @DeleteMapping("/batch/{ids}")
    @RequirePermission(roles = { "admin" }, businessType = "category", paramSource = "path_single", paramNames = {
            "ids" })
    @ApiLog("批量删除分类")
    public Result deleteCategories(@PathVariable String ids) {
        List<Long> idList = Arrays.stream(ids.split(","))
                .map(String::trim)
                .filter(s -> !s.isEmpty())
                .map(Long::valueOf)
                .toList();
        categoryService.deleteCategories(idList);
        return Result.success();
    }

    @Operation(summary = "新增子分类")
    @PostMapping("/sub")
    @RequirePermission(roles = { "admin" }, businessType = "subcategory", paramSource = "body", paramNames = { "id" })
    @ApiLog("新增子分类")
    public Result addSubCategory(@Validated @RequestBody SubCategoryCreateDTO dto) {
        categoryService.addSubCategory(dto);
        return Result.success();
    }

    @Operation(summary = "修改子分类")
    @PutMapping("/sub")
    @RequirePermission(roles = { "admin" }, businessType = "subcategory", paramSource = "body", paramNames = { "id" })
    @ApiLog("修改子分类")
    public Result updateSubCategory(@Validated @RequestBody SubCategoryUpdateDTO dto) {
        categoryService.updateSubCategory(dto);
        return Result.success();
    }

    @Operation(summary = "删除子分类")
    @DeleteMapping("/sub/{id}")
    @RequirePermission(roles = { "admin" }, businessType = "subcategory", paramSource = "path_single", paramNames = {
            "id" })
    @ApiLog("删除子分类")
    public Result deleteSubCategory(@PathVariable Long id) {
        categoryService.deleteSubCategory(id);
        return Result.success();
    }

    @Operation(summary = "批量删除子分类")
    @DeleteMapping("/sub/batch/{ids}")
    @RequirePermission(roles = { "admin" }, businessType = "subcategory", paramSource = "path_single", paramNames = {
            "ids" })
    @ApiLog("批量删除子分类")
    public Result deleteSubCategories(@PathVariable String ids) {
        List<Long> idList = Arrays.stream(ids.split(","))
                .map(String::trim)
                .filter(s -> !s.isEmpty())
                .map(Long::valueOf)
                .toList();
        for (Long id : idList) {
            categoryService.deleteSubCategory(id);
        }
        return Result.success();
    }

    @Operation(summary = "分页查询分类（含子分类信息）")
    @GetMapping("/list")
    @ApiLog("分页查询分类")
    public Result pageCategory(@RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size) {
        IPage<CategoryVO> resultPage = categoryService.pageCategory(new Page<>(page, size));
        return Result.success(Map.of(
                "list", resultPage.getRecords(),
                "total", resultPage.getTotal()));
    }

    @Operation(summary = "根据ID查询分类（含子分类信息）")
    @GetMapping("/{id}")
    @ApiLog("根据ID查询分类")
    public Result getCategoryById(@PathVariable Long id) {
        CategoryVO vo = categoryService.getCategoryById(id);
        if (vo == null) {
            return Result.error("分类不存在");
        }
        return Result.success(vo);
    }
}
