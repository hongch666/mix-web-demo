package com.hcsy.spring.api.controller;

import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.hcsy.spring.api.service.ArticleCollectService;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.core.annotation.ApiLog;
import com.hcsy.spring.core.annotation.Neo4jSync;
import com.hcsy.spring.entity.dto.ArticleCollectDTO;
import com.hcsy.spring.entity.vo.ArticleCollectVO;
import com.hcsy.spring.entity.vo.CollectCheckVO;
import com.hcsy.spring.entity.vo.CollectCountVO;
import com.hcsy.spring.entity.vo.PageVO;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;

@RestController
@RequestMapping("/collects")
@RequiredArgsConstructor
@Tag(name = "文章收藏模块", description = "文章收藏功能相关API，包括收藏、取消收藏、收藏列表查询、收藏统计等")
public class ArticleCollectController {

    private final ArticleCollectService articleCollectService;

    @PostMapping
    @Operation(summary = "添加收藏", description = "为文章添加收藏")
    @Neo4jSync(description = Messages.NEO4J_SYNC_DESC_COLLECT)
    @ApiLog("添加收藏")
    public Mono<Result<Void>> addCollect(@Valid @RequestBody ArticleCollectDTO dto) {
        return articleCollectService.addCollect(dto.getArticleId(), dto.getUserId())
                .map(success -> success ? Result.<Void>success()
                        : Result.<Void>error(HttpCode.CONFLICT, Messages.COLLECT_FAIL));
    }

    @DeleteMapping
    @Operation(summary = "取消收藏", description = "取消对文章的收藏")
    @Neo4jSync(description = Messages.NEO4J_SYNC_DESC_UNCOLLECT)
    @ApiLog("取消收藏")
    public Mono<Result<Void>> removeCollect(
            @Parameter(description = "文章ID", required = true) @RequestParam(value = "article_id", required = true) Long articleId,
            @Parameter(description = "用户ID", required = true) @RequestParam(value = "user_id", required = true) Long userId) {
        return articleCollectService.removeCollect(articleId, userId)
                .map(success -> success ? Result.<Void>success()
                        : Result.<Void>error(HttpCode.CONFLICT, Messages.UNCOLLECT_FAIL));
    }

    @GetMapping("/user/{user_id}")
    @Operation(summary = "查询用户的所有收藏", description = "分页查询某个用户的所有收藏记录（包含文章详情）")
    @ApiLog("查询用户收藏")
    public Mono<Result<PageVO<ArticleCollectVO>>> listUserCollects(
            @Parameter(description = "用户ID", required = true) @PathVariable("user_id") Long userId,
            @Parameter(description = "页码", required = false) @RequestParam(defaultValue = "1") int page,
            @Parameter(description = "每页数量", required = false) @RequestParam(defaultValue = "10") int size) {
        return articleCollectService.listUserCollects(userId, page, size)
                .map(result -> Result.success(new PageVO<>(result.getTotal(), result.getRecords())));
    }

    @GetMapping("/check")
    @Operation(summary = "检查用户是否收藏", description = "查询用户是否收藏过某篇文章")
    @ApiLog("检查收藏状态")
    public Mono<Result<CollectCheckVO>> isCollected(
            @Parameter(description = "文章ID", required = true) @RequestParam(value = "article_id", required = true) Long articleId,
            @Parameter(description = "用户ID", required = true) @RequestParam(value = "user_id", required = true) Long userId) {
        return articleCollectService.isCollected(articleId, userId)
                .map(collected -> Result.success(new CollectCheckVO(collected)));
    }

    @GetMapping("/count/{article_id}")
    @Operation(summary = "获取文章的收藏数", description = "获取某篇文章的总收藏数")
    @ApiLog("获取收藏数")
    public Mono<Result<CollectCountVO>> getCollectCount(
            @Parameter(description = "文章ID", required = true) @PathVariable("article_id") Long articleId) {
        return articleCollectService.getCollectCountByArticleId(articleId)
                .map(count -> Result.success(new CollectCountVO(count)));
    }
}
