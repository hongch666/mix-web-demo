package com.hcsy.spring.controller;

import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.hcsy.spring.dto.CategoryCreateDTO;
import com.hcsy.spring.dto.CategoryUpdateDTO;
import com.hcsy.spring.dto.SubCategoryCreateDTO;
import com.hcsy.spring.dto.SubCategoryUpdateDTO;
import com.hcsy.spring.service.CategoryService;
import com.hcsy.spring.vo.CategoryVO;
import io.swagger.v3.oas.annotations.Operation;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import com.hcsy.spring.po.Result;
import java.util.List;
import java.util.Map;
import java.util.Arrays;

@RestController
@RequestMapping("/category")
@RequiredArgsConstructor
@Slf4j
@Tag(name = "分类模块", description = "分类相关接口")
public class CategoryController {

    private final CategoryService categoryService;

    @Operation(summary = "新增分类")
    @PostMapping()
    public Result addCategory(@Validated @RequestBody CategoryCreateDTO dto) {
        categoryService.addCategory(dto);
        return Result.success();
    }

    @Operation(summary = "修改分类")
    @PutMapping()
    public Result updateCategory(@Validated @RequestBody CategoryUpdateDTO dto) {
        categoryService.updateCategory(dto);
        return Result.success();
    }

    @Operation(summary = "删除分类（级联删除子分类）")
    @DeleteMapping("/{id}")
    public Result deleteCategory(@PathVariable Long id) {
        categoryService.deleteCategory(id);
        return Result.success();
    }

    @Operation(summary = "批量删除分类（级联删除子分类）")
    @DeleteMapping("/batch/{ids}")
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
    public Result addSubCategory(@Validated @RequestBody SubCategoryCreateDTO dto) {
        categoryService.addSubCategory(dto);
        return Result.success();
    }

    @Operation(summary = "修改子分类")
    @PutMapping("/sub")
    public Result updateSubCategory(@Validated @RequestBody SubCategoryUpdateDTO dto) {
        categoryService.updateSubCategory(dto);
        return Result.success();
    }

    @Operation(summary = "删除子分类")
    @DeleteMapping("/sub/{id}")
    public Result deleteSubCategory(@PathVariable Long id) {
        categoryService.deleteSubCategory(id);
        return Result.success();
    }

    @Operation(summary = "批量删除子分类")
    @DeleteMapping("/sub/batch/{ids}")
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
    public Result pageCategory(@RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size) {
        IPage<CategoryVO> resultPage = categoryService.pageCategory(new Page<>(page, size));
        return Result.success(Map.of(
                "list", resultPage.getRecords(),
                "total", resultPage.getTotal()));
    }

    @Operation(summary = "根据ID查询分类（含子分类信息）")
    @GetMapping("/{id}")
    public Result getCategoryById(@PathVariable Long id) {
        CategoryVO vo = categoryService.getCategoryById(id);
        if (vo == null) {
            return Result.error("分类不存在");
        }
        return Result.success(vo);
    }
}
