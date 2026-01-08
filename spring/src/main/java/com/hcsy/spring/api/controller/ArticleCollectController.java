package com.hcsy.spring.api.controller;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.hcsy.spring.api.service.ArticleCollectService;
import com.hcsy.spring.common.annotation.ApiLog;
import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.entity.dto.ArticleCollectDTO;
import com.hcsy.spring.entity.po.ArticleCollect;
import com.hcsy.spring.entity.vo.ArticleCollectVO;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import io.swagger.v3.oas.annotations.Parameter;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/collects")
@RequiredArgsConstructor
@Tag(name = "文章收藏模块", description = "文章收藏相关接口")
public class ArticleCollectController {

    private final ArticleCollectService articleCollectService;

    @PostMapping
    @Operation(summary = "添加收藏", description = "为文章添加收藏")
    @ApiLog("添加收藏")
    public Result addCollect(@Valid @RequestBody ArticleCollectDTO dto) {
        boolean success = articleCollectService.addCollect(dto.getArticleId(), dto.getUserId());
        if (success) {
            return Result.success();
        } else {
            return Result.error("收藏失败，可能已经收藏过了");
        }
    }

    @DeleteMapping
    @Operation(summary = "取消收藏", description = "取消对文章的收藏")
    @ApiLog("取消收藏")
    public Result removeCollect(
            @Parameter(description = "文章ID", required = true) @RequestParam(required = true) Long articleId,
            @Parameter(description = "用户ID", required = true) @RequestParam(required = true) Long userId) {
        boolean success = articleCollectService.removeCollect(articleId, userId);
        if (success) {
            return Result.success();
        } else {
            return Result.error("取消收藏失败，记录不存在");
        }
    }

    @GetMapping("/user/{userId}")
    @Operation(summary = "查询用户的所有收藏", description = "分页查询某个用户的所有收藏记录（包含文章详情）")
    @ApiLog("查询用户收藏")
    public Result listUserCollects(
            @Parameter(description = "用户ID", required = true) @PathVariable Long userId,
            @Parameter(description = "页码", required = false) @RequestParam(defaultValue = "1") int page,
            @Parameter(description = "每页数量", required = false) @RequestParam(defaultValue = "10") int size) {
        Page<ArticleCollect> pageRequest = new Page<>(page, size);
        IPage<ArticleCollectVO> result = articleCollectService.listUserCollects(userId, pageRequest);

        Map<String, Object> data = new HashMap<>();
        data.put("total", result.getTotal());
        data.put("list", result.getRecords());
        return Result.success(data);
    }

    @GetMapping("/check")
    @Operation(summary = "检查用户是否收藏", description = "查询用户是否收藏过某篇文章")
    @ApiLog("检查收藏状态")
    public Result isCollected(
            @Parameter(description = "文章ID", required = true) @RequestParam(required = true) Long articleId,
            @Parameter(description = "用户ID", required = true) @RequestParam(required = true) Long userId) {
        boolean collected = articleCollectService.isCollected(articleId, userId);
        Map<String, Object> data = new HashMap<>();
        data.put("collected", collected);
        return Result.success(data);
    }

    @GetMapping("/count/{articleId}")
    @Operation(summary = "获取文章的收藏数", description = "获取某篇文章的总收藏数")
    @ApiLog("获取收藏数")
    public Result getCollectCount(
            @Parameter(description = "文章ID", required = true) @PathVariable Long articleId) {
        Long count = articleCollectService.getCollectCountByArticleId(articleId);
        Map<String, Object> data = new HashMap<>();
        data.put("collectCount", count);
        return Result.success(data);
    }
}
