package com.hcsy.spring.api.controller;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.hcsy.spring.entity.dto.ArticleCreateDTO;
import com.hcsy.spring.entity.dto.ArticleUpdateDTO;
import com.hcsy.spring.entity.po.Article;
import com.hcsy.spring.entity.po.Category;
import com.hcsy.spring.entity.po.Result;
import com.hcsy.spring.entity.po.SubCategory;
import com.hcsy.spring.entity.po.User;
import com.hcsy.spring.api.mapper.CategoryMapper;
import com.hcsy.spring.api.mapper.SubCategoryMapper;
import com.hcsy.spring.api.service.ArticleService;
import com.hcsy.spring.api.service.UserService;
import com.hcsy.spring.common.annotation.ApiLog;
import com.hcsy.spring.common.utils.UserContext;

import cn.hutool.core.bean.BeanUtil;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

import java.util.HashMap;
import java.util.Map;
import java.util.Arrays;
import java.util.List;
import java.util.ArrayList;
import com.hcsy.spring.entity.vo.ArticleWithCategoryVO;

import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/articles")
@RequiredArgsConstructor
@Slf4j
@Tag(name = "文章模块", description = "文章相关接口")
public class ArticleController {

    private final ArticleService articleService;
    private final UserService userService;
    private final CategoryMapper categoryMapper;
    private final SubCategoryMapper subCategoryMapper;

    @PostMapping
    @Operation(summary = "创建文章", description = "通过请求体创建一篇新文章")
    @ApiLog("创建文章")
    public Result createArticle(@Valid @RequestBody ArticleCreateDTO dto) {
        Article article = BeanUtil.copyProperties(dto, Article.class);
        // 获取用户id
        User user = userService.findByUsername(dto.getUsername());
        if (user == null) {
            return Result.error("用户不存在");
        }
        article.setUserId(user.getId());
        article.setViews(0);
        articleService.saveArticle(article);
        return Result.success();
    }

    @GetMapping("/list")
    @Operation(summary = "获取文章列表", description = "返回所有已发布的文章")
    @ApiLog("获取已发布文章列表")
    public Result getPublishedArticles(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size) {
        Page<Article> articlePage = new Page<>(page, size);
        IPage<Article> resultPage = articleService.listPublishedArticles(articlePage);

        Map<String, Object> data = new HashMap<>();
        data.put("total", resultPage.getTotal());
        data.put("list", resultPage.getRecords());
        return Result.success(data);
    }

    @GetMapping("user/{id}")
    @Operation(summary = "获取用户所有文章", description = "返回用户所有文章")
    @ApiLog("获取用户所有文章")
    public Result getPublishedArticles(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size,
            @PathVariable Integer id) {
        Page<Article> articlePage = new Page<>(page, size);
        IPage<Article> resultPage = articleService.listArticlesById(articlePage, id);

        List<Article> records = resultPage.getRecords();
        List<ArticleWithCategoryVO> voList = new ArrayList<>();
        for (Article article : records) {
            if (article.getSubCategoryId() == null) {
                return Result.error("子分类ID不能为空");
            }

            ArticleWithCategoryVO vo = BeanUtil.copyProperties(article, ArticleWithCategoryVO.class);

            // 查询作者用户名
            Long userId = UserContext.getUserId();
            User user = userService.getById(userId);
            vo.setUsername(user != null ? user.getName() : "");
            // 查询子分类信息
            SubCategory subCategory = subCategoryMapper.selectById(article.getSubCategoryId());
            vo.setSubCategoryName(subCategory.getName());
            // 查询主分类信息
            Category category = categoryMapper.selectById(subCategory.getCategoryId());
            vo.setCategoryName(category.getName());

            voList.add(vo);
        }
        Map<String, Object> data = new HashMap<>();
        data.put("total", resultPage.getTotal());
        data.put("list", voList);
        return Result.success(data);
    }

    @GetMapping("/{id}")
    @Operation(summary = "获取文章详情", description = "根据ID获取文章详情")
    @ApiLog("获取文章详情")
    public Result getArticleById(@PathVariable Long id) {
        Article article = articleService.getById(id);
        if (article == null) {
            return Result.error("文章不存在");
        }
        ArticleWithCategoryVO vo = BeanUtil.copyProperties(article, ArticleWithCategoryVO.class);
        // 查询作者用户名
        User user = userService.getById(article.getUserId());
        String username = user != null ? user.getName() : null;
        vo.setUsername(username);

        return Result.success(vo);
    }

    @PutMapping
    @Operation(summary = "更新文章", description = "根据DTO更新文章信息")
    @ApiLog("更新文章")
    public Result updateArticle(@Valid @RequestBody ArticleUpdateDTO dto) {
        // 获取用户id
        User userFromUsername = userService.findByUsername(dto.getUsername());
        if (userFromUsername == null) {
            return Result.error("用户不存在");
        }

        Article article = BeanUtil.copyProperties(dto, Article.class);
        article.setUserId(userFromUsername.getId());
        Article dbArticle = articleService.getById(dto.getId());
        Long userId = UserContext.getUserId();
        User user = userService.getById(userId);
        if (dbArticle == null) {
            throw new RuntimeException("文章不存在");
        }
        if (!"admin".equals(user.getRole()) && !userId.equals(dbArticle.getUserId())) {
            throw new RuntimeException("无权修改他人文章");
        }
        articleService.updateArticle(article);
        return Result.success();
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "删除文章", description = "根据ID删除文章")
    @ApiLog("删除文章")
    public Result deleteArticle(@PathVariable Long id) {
        Long userId = UserContext.getUserId();
        Article dbArticle = articleService.getById(id);
        User user = userService.getById(userId);
        if (dbArticle == null) {
            throw new RuntimeException("文章不存在");
        }
        if (!"admin".equals(user.getRole()) && !userId.equals(dbArticle.getUserId())) {
            throw new RuntimeException("无权删除他人文章");
        }
        articleService.deleteArticle(id);
        return Result.success();
    }

    @DeleteMapping("/batch/{ids}")
    @Operation(summary = "批量删除文章", description = "根据ID数组批量删除文章，多个ID用英文逗号分隔")
    @ApiLog("批量删除文章")
    public Result deleteArticles(@PathVariable String ids) {
        Long userId = UserContext.getUserId();
        List<Long> idList = Arrays.stream(ids.split(","))
                .map(String::trim)
                .filter(s -> !s.isEmpty())
                .map(Long::valueOf)
                .toList();

        User user = userService.getById(userId);
        for (Long id : idList) {
            Article dbArticle = articleService.getById(id);
            if (dbArticle == null) {
                throw new RuntimeException("文章不存在");
            }
            if (!"admin".equals(user.getRole()) && !userId.equals(dbArticle.getUserId())) {
                throw new RuntimeException("无权删除他人文章");
            }
        }

        articleService.deleteArticles(idList);
        return Result.success();

    }

    @PutMapping("/publish/{id}")
    @Operation(summary = "发布文章", description = "将文章状态修改为发布")
    @ApiLog("发布文章")
    public Result publishArticle(@PathVariable Long id) {
        articleService.publishArticle(id);
        return Result.success();
    }

    @PutMapping("/view/{id}")
    @Operation(summary = "增加文章阅读量", description = "增加文章阅读量")
    @ApiLog("增加文章阅读量")
    public Result addViewArticle(@PathVariable Long id) {
        Article dbArticle = articleService.getById(id);
        if (dbArticle == null) {
            throw new RuntimeException("文章不存在");
        }
        articleService.addViewArticle(id);
        return Result.success();
    }

}
