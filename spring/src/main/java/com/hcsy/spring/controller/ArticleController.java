package com.hcsy.spring.controller;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.hcsy.spring.dto.ArticleCreateDTO;
import com.hcsy.spring.dto.ArticleUpdateDTO;
import com.hcsy.spring.po.Article;
import com.hcsy.spring.po.Result;
import com.hcsy.spring.service.ArticleService;
import cn.hutool.core.bean.BeanUtil;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;

import java.util.HashMap;
import java.util.Map;

import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/articles")
@RequiredArgsConstructor
@Tag(name = "文章模块", description = "文章相关接口")
public class ArticleController {

    private final ArticleService articleService;

    @PostMapping
    @Operation(summary = "创建文章", description = "通过请求体创建一篇新文章")
    public Result createArticle(@Valid @RequestBody ArticleCreateDTO dto) {
        Article article = BeanUtil.copyProperties(dto, Article.class);
        articleService.saveArticle(article);
        return Result.success();
    }

    @GetMapping
    @Operation(summary = "获取文章列表", description = "返回所有已发布的文章")
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
    public Result getPublishedArticles(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size,
            @PathVariable Integer id) {
        Page<Article> articlePage = new Page<>(page, size);
        IPage<Article> resultPage = articleService.listArticlesById(articlePage, id);

        Map<String, Object> data = new HashMap<>();
        data.put("total", resultPage.getTotal());
        data.put("list", resultPage.getRecords());
        return Result.success(data);
    }

    @GetMapping("/{id}")
    @Operation(summary = "获取文章详情", description = "根据ID获取文章详情")
    public Result getArticleById(@PathVariable Long id) {
        Article article = articleService.getById(id);
        return Result.success(article);
    }

    @PutMapping
    @Operation(summary = "更新文章", description = "根据DTO更新文章信息")
    public Result updateArticle(@Valid @RequestBody ArticleUpdateDTO dto) {
        Article article = BeanUtil.copyProperties(dto, Article.class);
        articleService.updateArticle(article);
        return Result.success();
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "删除文章", description = "根据ID删除文章")
    public Result deleteArticle(@PathVariable Long id) {
        articleService.deleteArticle(id);
        return Result.success();
    }
}
