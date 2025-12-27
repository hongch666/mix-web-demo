package com.hcsy.spring.api.controller;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.hcsy.spring.api.service.FocusService;
import com.hcsy.spring.common.annotation.ApiLog;
import com.hcsy.spring.entity.dto.FocusDTO;
import com.hcsy.spring.entity.po.Focus;
import com.hcsy.spring.entity.po.Result;
import com.hcsy.spring.entity.vo.FocusUserVO;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import io.swagger.v3.oas.annotations.Parameter;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/focus")
@RequiredArgsConstructor
@Tag(name = "用户关注模块", description = "用户关注相关接口")
public class FocusController {

    private final FocusService focusService;

    @PostMapping
    @Operation(summary = "新增关注", description = "用户关注另一个用户")
    @ApiLog("新增关注")
    public Result addFocus(@Valid @RequestBody FocusDTO dto) {
        boolean success = focusService.addFocus(dto.getUserId(), dto.getFocusId());
        if (success) {
            return Result.success();
        } else {
            return Result.error("关注失败，可能已经关注过了");
        }
    }

    @DeleteMapping
    @Operation(summary = "取消关注", description = "用户取消关注另一个用户")
    @ApiLog("取消关注")
    public Result removeFocus(
            @Parameter(description = "用户ID", required = true) @RequestParam(required = true) Long userId,
            @Parameter(description = "关注用户ID", required = true) @RequestParam(required = true) Long focusId) {
        boolean success = focusService.removeFocus(userId, focusId);
        if (success) {
            return Result.success();
        } else {
            return Result.error("取消关注失败，记录不存在");
        }
    }

    @GetMapping("/check")
    @Operation(summary = "检查关注状态", description = "查询用户是否关注了某个用户")
    @ApiLog("检查关注状态")
    public Result isFocused(
            @Parameter(description = "用户ID", required = true) @RequestParam(required = true) Long userId,
            @Parameter(description = "关注用户ID", required = true) @RequestParam(required = true) Long focusId) {
        boolean focused = focusService.isFocused(userId, focusId);
        Map<String, Object> data = new HashMap<>();
        data.put("focused", focused);
        return Result.success(data);
    }

    @GetMapping("/authors/{userId}")
    @Operation(summary = "查询用户的所有关注作者", description = "分页查询某个用户关注的所有作者信息")
    @ApiLog("查询用户关注")
    public Result listUserFocuses(
            @Parameter(description = "用户ID", required = true) @PathVariable Long userId,
            @Parameter(description = "页码", required = false) @RequestParam(defaultValue = "1") int page,
            @Parameter(description = "每页数量", required = false) @RequestParam(defaultValue = "10") int size) {
        Page<Focus> pageRequest = new Page<>(page, size);
        IPage<FocusUserVO> result = focusService.listUserFocuses(userId, pageRequest);

        Map<String, Object> data = new HashMap<>();
        data.put("total", result.getTotal());
        data.put("list", result.getRecords());
        return Result.success(data);
    }

    @GetMapping("/followers/{userId}")
    @Operation(summary = "查询用户的所有粉丝", description = "分页查询某个用户的所有粉丝信息")
    @ApiLog("查询用户粉丝")
    public Result listUserFollowers(
            @Parameter(description = "用户ID", required = true) @PathVariable Long userId,
            @Parameter(description = "页码", required = false) @RequestParam(defaultValue = "1") int page,
            @Parameter(description = "每页数量", required = false) @RequestParam(defaultValue = "10") int size) {
        Page<Focus> pageRequest = new Page<>(page, size);
        IPage<FocusUserVO> result = focusService.listUserFollowers(userId, pageRequest);

        Map<String, Object> data = new HashMap<>();
        data.put("total", result.getTotal());
        data.put("list", result.getRecords());
        return Result.success(data);
    }

    @GetMapping("/count/focus/{userId}")
    @Operation(summary = "获取用户的关注数", description = "查询用户关注的人数")
    @ApiLog("查询关注数")
    public Result getFocusCount(
            @Parameter(description = "用户ID", required = true) @PathVariable Long userId) {
        Long count = focusService.getFocusCountByUserId(userId);
        Map<String, Object> data = new HashMap<>();
        data.put("count", count);
        return Result.success(data);
    }

    @GetMapping("/count/follower/{userId}")
    @Operation(summary = "获取用户的粉丝数", description = "查询用户的粉丝数量")
    @ApiLog("查询粉丝数")
    public Result getFollowerCount(
            @Parameter(description = "用户ID", required = true) @PathVariable Long userId) {
        Long count = focusService.getFollowerCountByUserId(userId);
        Map<String, Object> data = new HashMap<>();
        data.put("count", count);
        return Result.success(data);
    }
}
