package com.hcsy.spring.api.controller;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.hcsy.spring.api.service.ArticleLikeService;
import com.hcsy.spring.common.annotation.ApiLog;
import com.hcsy.spring.common.utils.Constants;
import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.entity.dto.ArticleLikeDTO;
import com.hcsy.spring.entity.po.ArticleLike;
import com.hcsy.spring.entity.vo.ArticleLikeVO;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import io.swagger.v3.oas.annotations.Parameter;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/likes")
@RequiredArgsConstructor
@Tag(name = "文章点赞模块", description = "文章点赞相关接口")
public class ArticleLikeController {

    private final ArticleLikeService articleLikeService;

    @PostMapping
    @Operation(summary = "添加点赞", description = "为文章添加点赞")
    @ApiLog("添加点赞")
    public Result addLike(@Valid @RequestBody ArticleLikeDTO dto) {
        boolean success = articleLikeService.addLike(dto.getArticleId(), dto.getUserId());
        if (success) {
            return Result.success();
        } else {
            return Result.error(Constants.LIKE_FAIL);
        }
    }

    @DeleteMapping
    @Operation(summary = "取消点赞", description = "取消对文章的点赞")
    @ApiLog("取消点赞")
    public Result removeLike(
            @Parameter(description = "文章ID", required = true) @RequestParam(required = true) Long articleId,
            @Parameter(description = "用户ID", required = true) @RequestParam(required = true) Long userId) {
        boolean success = articleLikeService.removeLike(articleId, userId);
        if (success) {
            return Result.success();
        } else {
            return Result.error(Constants.UNLIKE_FAIL);
        }
    }

    @GetMapping("/user/{userId}")
    @Operation(summary = "查询用户的所有点赞", description = "分页查询某个用户的所有点赞记录（包含文章详情）")
    @ApiLog("查询用户点赞")
    public Result listUserLikes(
            @Parameter(description = "用户ID", required = true) @PathVariable Long userId,
            @Parameter(description = "页码", required = false) @RequestParam(defaultValue = "1") int page,
            @Parameter(description = "每页数量", required = false) @RequestParam(defaultValue = "10") int size) {
        Page<ArticleLike> pageRequest = new Page<>(page, size);
        IPage<ArticleLikeVO> result = articleLikeService.listUserLikes(userId, pageRequest);

        Map<String, Object> data = new HashMap<>();
        data.put("total", result.getTotal());
        data.put("list", result.getRecords());
        return Result.success(data);
    }

    @GetMapping("/check")
    @Operation(summary = "检查用户是否点赞", description = "查询用户是否点赞过某篇文章")
    @ApiLog("检查点赞状态")
    public Result isLiked(
            @Parameter(description = "文章ID", required = true) @RequestParam(required = true) Long articleId,
            @Parameter(description = "用户ID", required = true) @RequestParam(required = true) Long userId) {
        boolean liked = articleLikeService.isLiked(articleId, userId);
        Map<String, Object> data = new HashMap<>();
        data.put("liked", liked);
        return Result.success(data);
    }

    @GetMapping("/count/{articleId}")
    @Operation(summary = "获取文章的点赞数", description = "获取某篇文章的总点赞数")
    @ApiLog("获取点赞数")
    public Result getLikeCount(
            @Parameter(description = "文章ID", required = true) @PathVariable Long articleId) {
        Long count = articleLikeService.getLikeCountByArticleId(articleId);
        Map<String, Object> data = new HashMap<>();
        data.put("likeCount", count);
        return Result.success(data);
    }
}
