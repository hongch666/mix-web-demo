package com.hcsy.spring.api.controller;

import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

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
import com.hcsy.spring.entity.dto.BatchIdsDTO;
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
    @Neo4jSync(description = "新增文章后同步 Neo4j")
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
    @Neo4jSync(description = "编辑文章后同步 Neo4j")
    @ApiLog("更新文章")
    public Mono<Result<Void>> updateArticle(@Valid @RequestBody ArticleUpdateDTO dto) {
        return userService.findByUsername(dto.getUsername())
            .flatMap(user -> {
                Article article = BeanUtil.copyProperties(dto, Article.class);
                article.setUserId(user.getId());
                article.setUpdateAt(java.time.LocalDateTime.now());
                return articleService.updateArticle(article).thenReturn(Result.<Void>success());
            })
            .defaultIfEmpty(Result.<Void>error(HttpCode.NOT_FOUND, Messages.UNDEFINED_USER));
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "删除文章", description = "根据ID删除文章")
    @RequirePermission(roles = {
        "admin" }, allowSelf = true, businessType = "article", paramSource = "path_single", paramNames = { "id" })
    @Neo4jSync(description = "删除文章后同步 Neo4j")
    @ApiLog("删除文章")
    public Mono<Result<Void>> deleteArticle(@PathVariable Long id) {
        return articleService.deleteArticle(id).thenReturn(Result.<Void>success());
    }

    @DeleteMapping("/batch/{ids}")
    @Operation(summary = "批量删除文章", description = "根据ID数组批量删除文章，多个ID用英文逗号分隔")
    @RequirePermission(roles = { "admin" }, businessType = "article", paramSource = "path_single", paramNames = {
        "ids" })
    @Neo4jSync(description = "批量删除文章后同步 Neo4j")
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
    @Neo4jSync(description = "发布文章后同步 Neo4j")
    @ApiLog("发布文章")
    public Mono<Result<Void>> publishArticle(@PathVariable Long id) {
        return articleService.publishArticle(id).thenReturn(Result.<Void>success());
    }

    @PutMapping("/view/{id}")
    @Operation(summary = "增加文章阅读量", description = "增加文章阅读量")
    @Neo4jSync(description = "浏览文章后同步 Neo4j")
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

    @PostMapping("/batch")
    @Operation(summary = "批量查询文章（内部）", description = "根据ID列表批量查询文章，供内部服务远程调用")
    @RequireInternalToken
    @ApiLog("内部批量查询文章")
    public Mono<Result<List<ArticleWithCategoryVO>>> getArticleByIds(@Valid @RequestBody BatchIdsDTO dto) {
        return articleService.listByIds(dto.getIds())
            .collectList()
            .map(articles -> articles.stream()
                .map(article -> BeanUtil.copyProperties(article, ArticleWithCategoryVO.class))
                .collect(Collectors.toList()))
            .map(Result::success);
    }

    @GetMapping("/by-title")
    @Operation(summary = "根据标题模糊搜索文章（内部）", description = "根据标题模糊搜索，供内部服务远程调用")
    @RequireInternalToken
    @ApiLog("内部搜索文章")
    public Mono<Result<List<ArticleWithCategoryVO>>> getArticlesByTitle(@RequestParam String title) {
        return articleService.listAllArticlesByTitle(title)
            .collectList()
            .map(articles -> articles.stream()
                .map(article -> BeanUtil.copyProperties(article, ArticleWithCategoryVO.class))
                .collect(Collectors.toList()))
            .map(Result::success);
    }

    @PostMapping("/views/batch")
    @Operation(summary = "批量查询文章阅读量（内部）", description = "根据ID列表批量查询文章阅读量，供内部服务远程调用")
    @RequireInternalToken
    @ApiLog("内部批量查询文章阅读量")
    public Mono<Result<Map<Long, Integer>>> getArticleViewsByIds(@Valid @RequestBody BatchIdsDTO dto) {
        return articleService.getArticleViewsByIDs(dto.getIds())
            .map(Result::success);
    }

    // ==================== 统计接口 ====================

    @GetMapping("/statistics/total-views")
    @Operation(summary = "获取文章总阅读量（内部）", description = "获取所有文章的总阅读量，供内部服务远程调用")
    @RequireInternalToken
    @ApiLog("内部获取文章总阅读量")
    public Mono<Result<Integer>> getTotalViews() {
        return articleService.getTotalViews().map(Result::success);
    }

    @GetMapping("/statistics/total")
    @Operation(summary = "获取文章总数（内部）", description = "获取文章总数，供内部服务远程调用")
    @RequireInternalToken
    @ApiLog("内部获取文章总数")
    public Mono<Result<Long>> getTotalArticles() {
        return articleService.getTotalArticles().map(Result::success);
    }

    @GetMapping("/statistics/active-authors")
    @Operation(summary = "获取活跃作者数（内部）", description = "获取活跃作者数，供内部服务远程调用")
    @RequireInternalToken
    @ApiLog("内部获取活跃作者数")
    public Mono<Result<Long>> getActiveAuthors() {
        return articleService.getActiveAuthors().map(Result::success);
    }

    @GetMapping("/statistics/average-views")
    @Operation(summary = "获取平均阅读量（内部）", description = "获取平均阅读量，供内部服务远程调用")
    @RequireInternalToken
    @ApiLog("内部获取平均阅读量")
    public Mono<Result<Double>> getAverageViews() {
        return articleService.getAverageViews().map(Result::success);
    }

    @GetMapping("/statistics/excel-export")
    @Operation(summary = "获取导出Excel所需文章数据（内部）", description = "获取导出Excel所需文章数据，供内部服务远程调用")
    @RequireInternalToken
    @ApiLog("内部获取导出Excel数据")
    public Mono<Result<List<Map<String, Object>>>> getArticlesForExcelExport() {
        return articleService.getArticlesForExcelExport().map(Result::success);
    }

    @GetMapping("/statistics/top10")
    @Operation(summary = "获取Top10文章（内部）", description = "获取Top10文章（按阅读量降序），供内部服务远程调用")
    @RequireInternalToken
    @ApiLog("内部获取Top10文章")
    public Mono<Result<List<Map<String, Object>>>> getTop10Articles() {
        return articleService.getTop10Articles().map(Result::success);
    }

    @GetMapping("/statistics/category-count")
    @Operation(summary = "获取按子分类统计的文章数量（内部）", description = "获取按子分类统计的文章数量，供内部服务远程调用")
    @RequireInternalToken
    @ApiLog("内部获取分类文章数量统计")
    public Mono<Result<List<Map<String, Object>>>> getCategoryArticleCount() {
        return articleService.getCategoryArticleCount().map(Result::success);
    }

    @GetMapping("/statistics/monthly-publish-count")
    @Operation(summary = "获取最近24个月文章发布数量统计（内部）", description = "获取最近24个月文章发布数量统计，供内部服务远程调用")
    @RequireInternalToken
    @ApiLog("内部获取月度发布数量统计")
    public Mono<Result<List<Map<String, Object>>>> getMonthlyPublishCount() {
        return articleService.getMonthlyPublishCount().map(Result::success);
    }

}
