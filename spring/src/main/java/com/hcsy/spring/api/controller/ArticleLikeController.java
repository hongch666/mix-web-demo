package com.hcsy.spring.api.controller;

import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.hcsy.spring.api.service.ArticleLikeService;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.core.annotation.ApiLog;
import com.hcsy.spring.core.annotation.Neo4jSync;
import com.hcsy.spring.entity.dto.ArticleLikeDTO;
import com.hcsy.spring.entity.po.ArticleLike;
import com.hcsy.spring.entity.vo.ArticleLikeVO;
import com.hcsy.spring.entity.vo.LikeCheckVO;
import com.hcsy.spring.entity.vo.LikeCountVO;
import com.hcsy.spring.entity.vo.PageVO;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;

@RestController
@RequestMapping("/likes")
@RequiredArgsConstructor
@Tag(name = "文章点赞模块", description = "文章点赞功能相关API，包括文章点赞、取消点赞、点赞状态查询、点赞统计等")
public class ArticleLikeController {

    private final ArticleLikeService articleLikeService;

    @PostMapping
    @Operation(summary = "添加点赞", description = "为文章添加点赞")
    @Neo4jSync(description = Messages.NEO4J_SYNC_DESC_LIKE)
    @ApiLog("添加点赞")
    public Mono<Result<Void>> addLike(@Valid @RequestBody ArticleLikeDTO dto) {
        return Mono.deferContextual(ctx -> {
            boolean success = articleLikeService.addLike(dto.getArticleId(), dto.getUserId());
            if (success) {
                return Mono.just(Result.<Void>success());
            } else {
                return Mono.just(Result.<Void>error(HttpCode.CONFLICT, Messages.LIKE_FAIL));
            }
        });
    }

    @DeleteMapping
    @Operation(summary = "取消点赞", description = "取消对文章的点赞")
    @Neo4jSync(description = Messages.NEO4J_SYNC_DESC_UNLIKE)
    @ApiLog("取消点赞")
    public Mono<Result<Void>> removeLike(
            @Parameter(description = "文章ID", required = true) @RequestParam(value = "article_id", required = true) Long articleId,
            @Parameter(description = "用户ID", required = true) @RequestParam(value = "user_id", required = true) Long userId) {
        return Mono.deferContextual(ctx -> {
            boolean success = articleLikeService.removeLike(articleId, userId);
            if (success) {
                return Mono.just(Result.<Void>success());
            } else {
                return Mono.just(Result.<Void>error(HttpCode.CONFLICT, Messages.UNLIKE_FAIL));
            }
        });
    }

    @GetMapping("/user/{user_id}")
    @Operation(summary = "查询用户的所有点赞", description = "分页查询某个用户的所有点赞记录（包含文章详情）")
    @ApiLog("查询用户点赞")
    public Mono<Result<PageVO<ArticleLikeVO>>> listUserLikes(
            @Parameter(description = "用户ID", required = true) @PathVariable("user_id") Long userId,
            @Parameter(description = "页码", required = false) @RequestParam(defaultValue = "1") int page,
            @Parameter(description = "每页数量", required = false) @RequestParam(defaultValue = "10") int size) {
        return Mono.deferContextual(ctx -> {
            Page<ArticleLike> pageRequest = new Page<>(page, size);
            IPage<ArticleLikeVO> result = articleLikeService.listUserLikes(userId, pageRequest);
            return Mono.just(Result.success(new PageVO<>(result.getTotal(), result.getRecords())));
        });
    }

    @GetMapping("/check")
    @Operation(summary = "检查用户是否点赞", description = "查询用户是否点赞过某篇文章")
    @ApiLog("检查点赞状态")
    public Mono<Result<LikeCheckVO>> isLiked(
            @Parameter(description = "文章ID", required = true) @RequestParam(value = "article_id", required = true) Long articleId,
            @Parameter(description = "用户ID", required = true) @RequestParam(value = "user_id", required = true) Long userId) {
        return Mono.deferContextual(ctx -> {
            boolean liked = articleLikeService.isLiked(articleId, userId);
            return Mono.just(Result.success(new LikeCheckVO(liked)));
        });
    }

    @GetMapping("/count/{article_id}")
    @Operation(summary = "获取文章的点赞数", description = "获取某篇文章的总点赞数")
    @ApiLog("获取点赞数")
    public Mono<Result<LikeCountVO>> getLikeCount(
            @Parameter(description = "文章ID", required = true) @PathVariable("article_id") Long articleId) {
        return Mono.deferContextual(ctx -> {
            Long count = articleLikeService.getLikeCountByArticleId(articleId);
            return Mono.just(Result.success(new LikeCountVO(count)));
        });
    }
}
