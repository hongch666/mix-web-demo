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
import com.hcsy.spring.api.service.FocusService;
import com.hcsy.spring.common.utils.Constants;
import com.hcsy.spring.common.utils.HttpCode;
import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.core.annotation.ApiLog;
import com.hcsy.spring.core.annotation.Neo4jSync;
import com.hcsy.spring.entity.dto.FocusDTO;
import com.hcsy.spring.entity.po.Focus;
import com.hcsy.spring.entity.vo.CountVO;
import com.hcsy.spring.entity.vo.FocusCheckVO;
import com.hcsy.spring.entity.vo.FocusUserVO;
import com.hcsy.spring.entity.vo.PageVO;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;

@RestController
@RequestMapping("/focus")
@RequiredArgsConstructor
@Tag(name = "用户关注模块", description = "用户关注功能相关API，包括关注、取消关注、关注列表、粉丝列表、关注统计等")
public class FocusController {

    private final FocusService focusService;

    @PostMapping
    @Operation(summary = "新增关注", description = "用户关注另一个用户")
    @Neo4jSync(description = Constants.NEO4J_SYNC_DESC_FOCUS)
    @ApiLog("新增关注")
    public Result addFocus(@Valid @RequestBody FocusDTO dto) {
        boolean success = focusService.addFocus(dto.getUserId(), dto.getFocusId());
        if (success) {
            return Result.success();
        } else {
            return Result.error(HttpCode.CONFLICT, Constants.FOCUS_FAIL);
        }
    }

    @DeleteMapping
    @Operation(summary = "取消关注", description = "用户取消关注另一个用户")
    @Neo4jSync(description = Constants.NEO4J_SYNC_DESC_UNFOCUS)
    @ApiLog("取消关注")
    public Result removeFocus(
            @Parameter(description = "用户ID", required = true) @RequestParam(value = "user_id", required = true) Long userId,
            @Parameter(description = "关注用户ID", required = true) @RequestParam(value = "focus_id", required = true) Long focusId) {
        boolean success = focusService.removeFocus(userId, focusId);
        if (success) {
            return Result.success();
        } else {
            return Result.error(HttpCode.CONFLICT, Constants.UNFOCUS_FAIL);
        }
    }

    @GetMapping("/check")
    @Operation(summary = "检查关注状态", description = "查询用户是否关注了某个用户")
    @ApiLog("检查关注状态")
    public Result isFocused(
            @Parameter(description = "用户ID", required = true) @RequestParam(value = "user_id", required = true) Long userId,
            @Parameter(description = "关注用户ID", required = true) @RequestParam(value = "focus_id", required = true) Long focusId) {
        boolean focused = focusService.isFocused(userId, focusId);
        return Result.success(new FocusCheckVO(focused));
    }

    @GetMapping("/authors/{user_id}")
    @Operation(summary = "查询用户的所有关注作者", description = "分页查询某个用户关注的所有作者信息")
    @ApiLog("查询用户关注")
    public Result listUserFocuses(
            @Parameter(description = "用户ID", required = true) @PathVariable("user_id") Long userId,
            @Parameter(description = "页码", required = false) @RequestParam(defaultValue = "1") int page,
            @Parameter(description = "每页数量", required = false) @RequestParam(defaultValue = "10") int size) {
        Page<Focus> pageRequest = new Page<>(page, size);
        IPage<FocusUserVO> result = focusService.listUserFocuses(userId, pageRequest);

        return Result.success(new PageVO<>(result.getTotal(), result.getRecords()));
    }

    @GetMapping("/followers/{user_id}")
    @Operation(summary = "查询用户的所有粉丝", description = "分页查询某个用户的所有粉丝信息")
    @ApiLog("查询用户粉丝")
    public Result listUserFollowers(
            @Parameter(description = "用户ID", required = true) @PathVariable("user_id") Long userId,
            @Parameter(description = "页码", required = false) @RequestParam(defaultValue = "1") int page,
            @Parameter(description = "每页数量", required = false) @RequestParam(defaultValue = "10") int size) {
        Page<Focus> pageRequest = new Page<>(page, size);
        IPage<FocusUserVO> result = focusService.listUserFollowers(userId, pageRequest);

        return Result.success(new PageVO<>(result.getTotal(), result.getRecords()));
    }

    @GetMapping("/count/focus/{user_id}")
    @Operation(summary = "获取用户的关注数", description = "查询用户关注的人数")
    @ApiLog("查询关注数")
    public Result getFocusCount(
            @Parameter(description = "用户ID", required = true) @PathVariable("user_id") Long userId) {
        Long count = focusService.getFocusCountByUserId(userId);
        return Result.success(new CountVO(count));
    }

    @GetMapping("/count/follower/{user_id}")
    @Operation(summary = "获取用户的粉丝数", description = "查询用户的粉丝数量")
    @ApiLog("查询粉丝数")
    public Result getFollowerCount(
            @Parameter(description = "用户ID", required = true) @PathVariable("user_id") Long userId) {
        Long count = focusService.getFollowerCountByUserId(userId);
        return Result.success(new CountVO(count));
    }
}
