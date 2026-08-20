package com.hcsy.spring.api.controller;

import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.hcsy.spring.api.service.ArticleService;
import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.core.annotation.ApiLog;
import com.hcsy.spring.core.annotation.RequireInternalToken;
import com.hcsy.spring.entity.dto.BatchIdsDTO;
import com.hcsy.spring.entity.vo.ArticleWithCategoryVO;

import cn.hutool.core.bean.BeanUtil;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;

/**
 * 文章模块内部接口（供 NestJS 服务远程调用）
 */
@RestController
@RequestMapping("/articles/internal")
@RequiredArgsConstructor
@Tag(name = "文章内部接口", description = "供 NestJS 服务远程调用的文章内部接口")
public class ArticleInternalController {

    private final ArticleService articleService;

    @GetMapping("/{id}")
    @Operation(summary = "根据ID查询文章（内部）", description = "根据ID查询文章，供 NestJS 服务远程调用")
    @RequireInternalToken
    @ApiLog("内部查询文章")
    public Mono<Result<ArticleWithCategoryVO>> getArticleById(@PathVariable Long id) {
        return articleService.getById(id)
            .map(article -> {
                ArticleWithCategoryVO vo = BeanUtil.copyProperties(article, ArticleWithCategoryVO.class);
                return Result.success(vo);
            })
            .defaultIfEmpty(Result.<ArticleWithCategoryVO>error(HttpCode.NOT_FOUND, Messages.UNDEFINED_ARTICLE));
    }

    @PostMapping("/batch")
    @Operation(summary = "批量查询文章（内部）", description = "根据ID列表批量查询文章，供 NestJS 服务远程调用")
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
    @Operation(summary = "根据标题模糊搜索文章（内部）", description = "根据标题模糊搜索，供 NestJS 服务远程调用")
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

    @GetMapping("/neo4j-sync")
    @Operation(summary = "获取文章表数据用于Neo4j同步（内部）", description = "获取文章表数据，支持增量同步，供FastAPI同步Neo4j使用")
    @RequireInternalToken
    @ApiLog("内部获取Neo4j同步文章数据")
    public Mono<Result<List<Map<String, Object>>>> getNeo4jSyncArticles(
        @RequestParam(required = false) String updatedAfter) {
        return articleService.getNeo4jSyncArticles(updatedAfter).map(Result::success);
    }
}
