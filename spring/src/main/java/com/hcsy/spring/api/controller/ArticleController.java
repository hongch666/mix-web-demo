package com.hcsy.spring.api.controller;

import java.util.Arrays;
import java.util.List;

import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.hcsy.spring.api.service.ArticleService;
import com.hcsy.spring.api.service.UserService;
import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.core.annotation.ApiLog;
import com.hcsy.spring.core.annotation.Neo4jSync;
import com.hcsy.spring.core.annotation.RequireInternalToken;
import com.hcsy.spring.core.annotation.RequirePermission;
import com.hcsy.spring.entity.dto.ArticleCreateDTO;
import com.hcsy.spring.entity.dto.ArticleUpdateDTO;
import com.hcsy.spring.entity.po.Article;
import com.hcsy.spring.entity.vo.ArticleWithCategoryVO;
import com.hcsy.spring.entity.vo.PageVO;

import cn.hutool.core.bean.BeanUtil;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;

@RestController
@RequestMapping("/articles")
@RequiredArgsConstructor
@Tag(name = "文章模块", description = "文章管理功能相关API，包括文章增删改查、搜索排序等")
public class ArticleController {

    private final ArticleService articleService;
    private final UserService userService;

    @PostMapping
    @Operation(summary = "创建文章", description = "通过请求体创建一篇新文章")
    @Neo4jSync(description = Messages.NEO4J_SYNC_DESC_ARTICLE_CREATE)
    @ApiLog("创建文章")
    public Mono<Result<Void>> createArticle(@Valid @RequestBody ArticleCreateDTO dto) {
        return userService.findByUsername(dto.getUsername())
                .flatMap(user -> {
                    Article article = BeanUtil.copyProperties(dto, Article.class);
                    article.setUserId(user.getId());
                    article.setViews(0);
                    return articleService.saveArticle(article).thenReturn(Result.<Void>success());
                })
                .defaultIfEmpty(Result.<Void>error(HttpCode.NOT_FOUND, Messages.UNDEFINED_USER));
    }

    @GetMapping("/list")
    @Operation(summary = "获取文章列表", description = "返回所有已发布的文章")
    @RequireInternalToken
    @ApiLog("获取已发布文章列表")
    public Mono<Result<PageVO<Article>>> getPublishedArticles(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size) {
        return articleService.listPublishedArticles(page, size)
                .map(result -> Result.success(new PageVO<>(result.getTotal(), result.getRecords())));
    }

    @GetMapping("user/{id}")
    @Operation(summary = "获取用户文章", description = "返回用户文章，可指定是否只查询已发布的文章")
    @ApiLog("获取用户文章")
    public Mono<Result<PageVO<ArticleWithCategoryVO>>> getArticlesByUserId(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size,
            @PathVariable Long id,
            @RequestParam(defaultValue = "0") int published) {
        return articleService.listArticlesByIdWithCategory(page, size, id, published == 1)
                .map(result -> Result.success(new PageVO<>(result.getTotal(), result.getRecords())));
    }

    @GetMapping("/{id}")
    @Operation(summary = "获取文章详情", description = "根据ID获取文章详情")
    @ApiLog("获取文章详情")
    public Mono<Result<ArticleWithCategoryVO>> getArticleById(@PathVariable Long id) {
        return articleService.getById(id)
                .flatMap(article -> userService.getById(article.getUserId())
                        .map(user -> {
                            ArticleWithCategoryVO vo = BeanUtil.copyProperties(article, ArticleWithCategoryVO.class);
                            vo.setUsername(user.getName());
                            return Result.success(vo);
                        })
                        .defaultIfEmpty(Result.success(BeanUtil.copyProperties(article, ArticleWithCategoryVO.class))))
                .defaultIfEmpty(Result.<ArticleWithCategoryVO>error(HttpCode.NOT_FOUND, Messages.UNDEFINED_ARTICLE));
    }

    @PutMapping
    @Operation(summary = "更新文章", description = "根据DTO更新文章信息")
    @RequirePermission(roles = {
            "admin" }, allowSelf = true, businessType = "article", paramSource = "body", paramNames = { "id" })
    @Neo4jSync(description = Messages.NEO4J_SYNC_DESC_ARTICLE_UPDATE)
    @ApiLog("更新文章")
    public Mono<Result<Void>> updateArticle(@Valid @RequestBody ArticleUpdateDTO dto) {
        return userService.findByUsername(dto.getUsername())
                .flatMap(user -> {
                    Article article = BeanUtil.copyProperties(dto, Article.class);
                    article.setUserId(user.getId());
                    return articleService.updateArticle(article).thenReturn(Result.<Void>success());
                })
                .defaultIfEmpty(Result.<Void>error(HttpCode.NOT_FOUND, Messages.UNDEFINED_USER));
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "删除文章", description = "根据ID删除文章")
    @RequirePermission(roles = {
            "admin" }, allowSelf = true, businessType = "article", paramSource = "path_single", paramNames = { "id" })
    @Neo4jSync(description = Messages.NEO4J_SYNC_DESC_ARTICLE_DELETE)
    @ApiLog("删除文章")
    public Mono<Result<Void>> deleteArticle(@PathVariable Long id) {
        return articleService.deleteArticle(id).thenReturn(Result.<Void>success());
    }

    @SuppressWarnings("null")
    @DeleteMapping("/batch/{ids}")
    @Operation(summary = "批量删除文章", description = "根据ID数组批量删除文章，多个ID用英文逗号分隔")
    @RequirePermission(roles = { "admin" }, businessType = "article", paramSource = "path_single", paramNames = {
            "ids" })
    @Neo4jSync(description = Messages.NEO4J_SYNC_DESC_ARTICLE_BATCH_DELETE)
    @ApiLog("批量删除文章")
    public Mono<Result<Void>> deleteArticles(@PathVariable String ids) {
        List<Long> idList = Arrays.stream(ids.split(","))
                .map(String::trim)
                .filter(s -> !s.isEmpty())
                .map(Long::valueOf)
                .toList();
        return articleService.deleteArticles(idList).thenReturn(Result.<Void>success());
    }

    @PutMapping("/publish/{id}")
    @Operation(summary = "发布文章", description = "将文章状态修改为发布")
    @RequirePermission(roles = { "admin" }, businessType = "article", paramSource = "path_single", paramNames = {
            "id" })
    @Neo4jSync(description = Messages.NEO4J_SYNC_DESC_ARTICLE_PUBLISH)
    @ApiLog("发布文章")
    public Mono<Result<Void>> publishArticle(@PathVariable Long id) {
        return articleService.publishArticle(id).thenReturn(Result.<Void>success());
    }

    @PutMapping("/view/{id}")
    @Operation(summary = "增加文章阅读量", description = "增加文章阅读量")
    @Neo4jSync(description = Messages.NEO4J_SYNC_DESC_ARTICLE_VIEW)
    @ApiLog("增加文章阅读量")
    public Mono<Result<Void>> addViewArticle(@PathVariable Long id) {
        return articleService.addViewArticle(id).thenReturn(Result.<Void>success());
    }

    @GetMapping("/unpublished/list")
    @Operation(summary = "获取所有未发布文章", description = "返回所有未发布的文章，支持分页")
    @ApiLog("获取未发布文章列表")
    public Mono<Result<PageVO<ArticleWithCategoryVO>>> getUnpublishedArticles(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size) {
        return articleService.listUnpublishedArticlesWithCategory(page, size)
                .map(result -> Result.success(new PageVO<>(result.getTotal(), result.getRecords())));
    }

}
