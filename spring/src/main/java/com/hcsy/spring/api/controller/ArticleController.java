package com.hcsy.spring.api.controller;

import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.hcsy.spring.api.service.ArticleService;
import com.hcsy.spring.api.service.UserService;
import com.hcsy.spring.common.exceptions.BusinessException;
import com.hcsy.spring.common.utils.Constants;
import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.core.annotation.ApiLog;
import com.hcsy.spring.core.annotation.RequireInternalToken;
import com.hcsy.spring.core.annotation.RequirePermission;
import com.hcsy.spring.entity.dto.ArticleCreateDTO;
import com.hcsy.spring.entity.dto.ArticleUpdateDTO;
import com.hcsy.spring.entity.po.Article;
import com.hcsy.spring.entity.po.User;
import com.hcsy.spring.entity.vo.ArticleWithCategoryVO;

import cn.hutool.core.bean.BeanUtil;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;

@RestController
@RequestMapping("/articles")
@RequiredArgsConstructor
@Tag(name = "文章模块", description = "文章相关接口")
public class ArticleController {

    private final ArticleService articleService;
    private final UserService userService;

    @PostMapping
    @Operation(summary = "创建文章", description = "通过请求体创建一篇新文章")
    @ApiLog("创建文章")
    public Result createArticle(@Valid @RequestBody ArticleCreateDTO dto) {
        Article article = BeanUtil.copyProperties(dto, Article.class);
        // 获取用户id
        User user = userService.findByUsername(dto.getUsername());
        if (user == null) {
            return Result.error(Constants.UNDEFINED_USER);
        }
        article.setUserId(user.getId());
        article.setViews(0);
        articleService.saveArticle(article);
        return Result.success();
    }

    @GetMapping("/list")
    @Operation(summary = "获取文章列表", description = "返回所有已发布的文章")
    @RequireInternalToken
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
    @Operation(summary = "获取用户文章", description = "返回用户文章，可指定是否只查询已发布的文章")
    @ApiLog("获取用户文章")
    public Result getArticlesByUserId(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size,
            @PathVariable Integer id,
            @RequestParam(defaultValue = "0") int published) {
        Page<Article> articlePage = new Page<>(page, size);
        IPage<ArticleWithCategoryVO> voPage = articleService.listArticlesByIdWithCategory(articlePage, id, published == 1);

        Map<String, Object> data = new HashMap<>();
        data.put("total", voPage.getTotal());
        data.put("list", voPage.getRecords());
        return Result.success(data);
    }

    @GetMapping("/{id}")
    @Operation(summary = "获取文章详情", description = "根据ID获取文章详情")
    @ApiLog("获取文章详情")
    public Result getArticleById(@PathVariable Long id) {
        Article article = articleService.getById(id);
        if (article == null) {
            return Result.error(Constants.UNDEFINED_ARTICLE);
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
    @RequirePermission(
        roles = { "admin" },
        allowSelf = true,
        businessType = "article",
        paramSource = "body",
        paramNames = { "id" }
    )
    @ApiLog("更新文章")
    public Result updateArticle(@Valid @RequestBody ArticleUpdateDTO dto) {
        // 获取用户id
        User userFromUsername = userService.findByUsername(dto.getUsername());
        if (userFromUsername == null) {
            return Result.error(Constants.UNDEFINED_USER);
        }

        Article article = BeanUtil.copyProperties(dto, Article.class);
        article.setUserId(userFromUsername.getId());
        articleService.updateArticle(article);
        return Result.success();
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "删除文章", description = "根据ID删除文章")
    @RequirePermission(
        roles = { "admin" },
        allowSelf = true,
        businessType = "article",
        paramSource = "path_single",
        paramNames = { "id" }
    )
    @ApiLog("删除文章")
    public Result deleteArticle(@PathVariable Long id) {
        articleService.deleteArticle(id);
        return Result.success();
    }

    @DeleteMapping("/batch/{ids}")
    @Operation(summary = "批量删除文章", description = "根据ID数组批量删除文章，多个ID用英文逗号分隔")
    @RequirePermission(
        roles = { "admin" },
        businessType = "article",
        paramSource = "path_single",
        paramNames = { "ids" }
    )
    @ApiLog("批量删除文章")
    public Result deleteArticles(@PathVariable String ids) {
        List<Long> idList = Arrays.stream(ids.split(","))
                .map(String::trim)
                .filter(s -> !s.isEmpty())
                .map(Long::valueOf)
                .toList();

        articleService.deleteArticles(idList);
        return Result.success();

    }

    @PutMapping("/publish/{id}")
    @Operation(summary = "发布文章", description = "将文章状态修改为发布")
    @RequirePermission(
        roles = { "admin" },
        businessType = "article",
        paramSource = "path_single",
        paramNames = { "id" }
    )
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
            throw new BusinessException(Constants.UNDEFINED_ARTICLE);
        }
        articleService.addViewArticle(id);
        return Result.success();
    }

    @GetMapping("/unpublished/list")
    @Operation(summary = "获取所有未发布文章", description = "返回所有未发布的文章，支持分页")
    @ApiLog("获取未发布文章列表")
    public Result getUnpublishedArticles(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size) {
        Page<Article> articlePage = new Page<>(page, size);
        IPage<ArticleWithCategoryVO> resultPage = articleService.listUnpublishedArticlesWithCategory(articlePage);

        Map<String, Object> data = new HashMap<>();
        data.put("total", resultPage.getTotal());
        data.put("list", resultPage.getRecords());
        return Result.success(data);
    }

}
