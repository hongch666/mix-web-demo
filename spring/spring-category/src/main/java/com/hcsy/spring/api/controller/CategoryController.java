package com.hcsy.spring.api.controller;

import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.hcsy.spring.api.mapper.CategoryMapper;
import com.hcsy.spring.api.mapper.SubCategoryMapper;
import com.hcsy.spring.api.service.CategoryService;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.common.utils.UserContext;
import com.hcsy.spring.entity.dto.CategoryCreateDTO;
import com.hcsy.spring.entity.dto.CategoryUpdateDTO;
import com.hcsy.spring.entity.dto.SubCategoryCreateDTO;
import com.hcsy.spring.entity.dto.SubCategoryUpdateDTO;
import com.hcsy.spring.entity.po.Category;
import com.hcsy.spring.entity.po.Result;
import com.hcsy.spring.entity.po.SubCategory;
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
@Slf4j
@Tag(name = "分类模块", description = "分类相关接口")
public class CategoryController {

    private final CategoryService categoryService;
    private final SimpleLogger logger;
    private final CategoryMapper categoryMapper;
    private final SubCategoryMapper subCategoryMapper;

    @Operation(summary = "新增分类")
    @PostMapping()
    public Result addCategory(@Validated @RequestBody CategoryCreateDTO dto) {
        Long userId = UserContext.getUserId();
        String userName = UserContext.getUsername();
        logger.info("用户" + userId + ":" + userName + " POST /category: " + "创建分类\nCategoryCreateDTO: %s", dto);
        categoryService.addCategory(dto);
        return Result.success();
    }

    @Operation(summary = "修改分类")
    @PutMapping()
    public Result updateCategory(@Validated @RequestBody CategoryUpdateDTO dto) {
        Long userId = UserContext.getUserId();
        String userName = UserContext.getUsername();
        logger.info("用户" + userId + ":" + userName + " PUT /category: " + "修改分类\nCategoryUpdateDTO: %s", dto);
        categoryService.updateCategory(dto);
        return Result.success();
    }

    @Operation(summary = "删除分类（级联删除子分类）")
    @DeleteMapping("/{id}")
    public Result deleteCategory(@PathVariable Long id) {
        Long userId = UserContext.getUserId();
        String userName = UserContext.getUsername();
        logger.info("用户" + userId + ":" + userName + " DELETE /category: " + "删除分类\nID: %d", id);
        categoryService.deleteCategory(id);
        return Result.success();
    }

    @Operation(summary = "批量删除分类（级联删除子分类）")
    @DeleteMapping("/batch/{ids}")
    public Result deleteCategories(@PathVariable String ids) {
        Long userId = UserContext.getUserId();
        String userName = UserContext.getUsername();
        logger.info("用户" + userId + ":" + userName + " DELETE /category: " + "批量删除分类\nIDs: %s", ids);
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
        Long userId = UserContext.getUserId();
        String userName = UserContext.getUsername();
        logger.info("用户" + userId + ":" + userName + " POST /category/sub: " + "新增子分类\nSubCategoryCreateDTO: %s", dto);
        categoryService.addSubCategory(dto);
        return Result.success();
    }

    @Operation(summary = "修改子分类")
    @PutMapping("/sub")
    public Result updateSubCategory(@Validated @RequestBody SubCategoryUpdateDTO dto) {
        Long userId = UserContext.getUserId();
        String userName = UserContext.getUsername();
        logger.info("用户" + userId + ":" + userName + " PUT /category/sub: " + "修改子分类\nSubCategoryUpdateDTO: %s", dto);
        categoryService.updateSubCategory(dto);
        return Result.success();
    }

    @Operation(summary = "删除子分类")
    @DeleteMapping("/sub/{id}")
    public Result deleteSubCategory(@PathVariable Long id) {
        Long userId = UserContext.getUserId();
        String userName = UserContext.getUsername();
        logger.info("用户" + userId + ":" + userName + " DELETE /category/sub: " + "删除子分类\nID: %d", id);
        categoryService.deleteSubCategory(id);
        return Result.success();
    }

    @Operation(summary = "批量删除子分类")
    @DeleteMapping("/sub/batch/{ids}")
    public Result deleteSubCategories(@PathVariable String ids) {
        Long userId = UserContext.getUserId();
        String userName = UserContext.getUsername();
        logger.info("用户" + userId + ":" + userName + " DELETE /category/sub: " + "批量删除子分类\nIDs: %s", ids);
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
        Long userId = UserContext.getUserId();
        String userName = UserContext.getUsername();
        logger.info("用户" + userId + ":" + userName + " GET /category/list: " + "分页查询分类\nPage: %d, Size: %d", page,
                size);
        IPage<CategoryVO> resultPage = categoryService.pageCategory(new Page<>(page, size));
        return Result.success(Map.of(
                "list", resultPage.getRecords(),
                "total", resultPage.getTotal()));
    }

    @Operation(summary = "根据ID查询分类（含子分类信息）")
    @GetMapping("/{id}")
    public Result getCategoryById(@PathVariable Long id) {
        Long userId = UserContext.getUserId();
        String userName = UserContext.getUsername();
        logger.info("用户" + userId + ":" + userName + " GET /category/%d: " + "根据ID查询分类\nID: %d", id, id);
        CategoryVO vo = categoryService.getCategoryById(id);
        if (vo == null) {
            return Result.error("分类不存在");
        }
        return Result.success(vo);
    }

    @Operation(summary = "根据ID数组查询分类数据")
    @GetMapping("/batch/{ids}")
    public Result getCategoriesByIds(@PathVariable String ids) {
        Long userId = UserContext.getUserId();
        String userName = UserContext.getUsername();
        logger.info("用户" + userId + ":" + userName + " GET /category/batch/%s: " + "根据ID数组查询分类数据\nIDs: %s", ids, ids);
        List<Long> idList = Arrays.stream(ids.split(","))
                .map(String::trim)
                .filter(s -> !s.isEmpty())
                .map(Long::valueOf)
                .toList();

        List<Object> categories = categoryService.getCategoriesById(idList);
        if (categories.isEmpty()) {
            return Result.error("未找到相关分类");
        }
        return Result.success(Map.of(
                "total", categories.size(),
                "list", categories));
    }

    @Operation(summary = "根据子分类ID数组查询子分类数据")
    @GetMapping("/sub/batch/{ids}")
    public Result getSubCategoriesByCategoryIds(@PathVariable String ids) {
        Long userId = UserContext.getUserId();
        String userName = UserContext.getUsername();
        logger.info("用户" + userId + ":" + userName + " GET /category/sub/batch/%s: "
                + "根据子分类ID数组查询子分类数据\nSubCategoryIDs: %s", ids, ids);
        List<Long> subCategoryIdList = Arrays.stream(ids.split(","))
                .map(String::trim)
                .filter(s -> !s.isEmpty())
                .map(Long::valueOf)
                .toList();

        List<Object> subCategories = categoryService.getSubCategoriesByIds(subCategoryIdList);
        return Result.success(Map.of(
                "total", subCategories.size(),
                "list", subCategories));
    }

    @Operation(summary = "查询所有父分类")
    @GetMapping("/all")
    public Result getAllCategories() {
        Long userId = UserContext.getUserId();
        String userName = UserContext.getUsername();
        logger.info("用户" + userId + ":" + userName + " GET /category/all: 查询所有父分类");
        List<Category> categories = categoryService.list();
        return Result.success(Map.of(
                "total", categories.size(),
                "list", categories));
    }

    @Operation(summary = "查询所有子分类")
    @GetMapping("/sub/all")
    public Result getAllSubCategories() {
        Long userId = UserContext.getUserId();
        String userName = UserContext.getUsername();
        logger.info("用户" + userId + ":" + userName + " GET /category/sub/all: 查询所有子分类");
        // 直接用IService<SubCategory>的list()
        List<SubCategory> subCategories = categoryService.listSubCategories();
        return Result.success(Map.of(
                "total", subCategories.size(),
                "list", subCategories));
    }

    @Operation(summary = "根据id查询父分类")
    @GetMapping("/single/{id}")
    public Result getSingleCategoryById(@PathVariable Long id) {
        Long userId = UserContext.getUserId();
        String userName = UserContext.getUsername();
        logger.info("用户" + userId + ":" + userName + " GET /category/single/%d: " + "根据ID查询父分类\nID: %d", id, id);
        Category vo = categoryMapper.selectById(id);
        if (vo == null) {
            return Result.error("分类不存在");
        }
        return Result.success(vo);
    }

    @Operation(summary = "根据id查询子分类")
    @GetMapping("/sub/single/{id}")
    public Result getSingleSubCategoryById(@PathVariable Long id) {
        Long userId = UserContext.getUserId();
        String userName = UserContext.getUsername();
        logger.info("用户" + userId + ":" + userName + " GET /category/sub/single/%d: " + "根据ID查询子分类\nID: %d", id, id);
        SubCategory vo = subCategoryMapper.selectById(id);
        if (vo == null) {
            return Result.error("子分类不存在");
        }
        return Result.success(vo);
    }
}
