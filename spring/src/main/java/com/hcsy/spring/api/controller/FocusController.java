package com.hcsy.spring.api.controller;

import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.hcsy.spring.api.service.FocusService;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.core.annotation.ApiLog;
import com.hcsy.spring.core.annotation.Neo4jSync;
import com.hcsy.spring.entity.dto.FocusDTO;
import com.hcsy.spring.entity.vo.CountVO;
import com.hcsy.spring.entity.vo.FocusCheckVO;
import com.hcsy.spring.entity.vo.FocusUserVO;
import com.hcsy.spring.entity.vo.PageVO;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;

@RestController
@RequestMapping("/focus")
@RequiredArgsConstructor
@Tag(name = "用户关注模块", description = "用户关注功能相关API，包括关注、取消关注、关注列表、粉丝列表、关注统计等")
public class FocusController {

    private final FocusService focusService;

    @PostMapping
    @Operation(summary = "新增关注", description = "用户关注另一个用户")
    @Neo4jSync(description = Messages.NEO4J_SYNC_DESC_FOCUS)
    @ApiLog("新增关注")
    public Mono<Result<Void>> addFocus(@Valid @RequestBody FocusDTO dto) {
        return focusService.addFocus(dto.getUserId(), dto.getFocusId())
                .map(success -> success ? Result.<Void>success()
                        : Result.<Void>error(HttpCode.CONFLICT, Messages.FOCUS_FAIL));
    }

    @DeleteMapping
    @Operation(summary = "取消关注", description = "用户取消关注另一个用户")
    @Neo4jSync(description = Messages.NEO4J_SYNC_DESC_UNFOCUS)
    @ApiLog("取消关注")
    public Mono<Result<Void>> removeFocus(
            @Parameter(description = "用户ID", required = true) @RequestParam(value = "user_id", required = true) Long userId,
            @Parameter(description = "关注用户ID", required = true) @RequestParam(value = "focus_id", required = true) Long focusId) {
        return focusService.removeFocus(userId, focusId)
                .map(success -> success ? Result.<Void>success()
                        : Result.<Void>error(HttpCode.CONFLICT, Messages.UNFOCUS_FAIL));
    }

    @GetMapping("/check")
    @Operation(summary = "检查关注状态", description = "查询用户是否关注了某个用户")
    @ApiLog("检查关注状态")
    public Mono<Result<FocusCheckVO>> isFocused(
            @Parameter(description = "用户ID", required = true) @RequestParam(value = "user_id", required = true) Long userId,
            @Parameter(description = "关注用户ID", required = true) @RequestParam(value = "focus_id", required = true) Long focusId) {
        return focusService.isFocused(userId, focusId)
                .map(focused -> Result.success(new FocusCheckVO(focused)));
    }

    @GetMapping("/authors/{user_id}")
    @Operation(summary = "查询用户的所有关注作者", description = "分页查询某个用户关注的所有作者信息")
    @ApiLog("查询用户关注")
    public Mono<Result<PageVO<FocusUserVO>>> listUserFocuses(
            @Parameter(description = "用户ID", required = true) @PathVariable("user_id") Long userId,
            @Parameter(description = "页码", required = false) @RequestParam(defaultValue = "1") int page,
            @Parameter(description = "每页数量", required = false) @RequestParam(defaultValue = "10") int size) {
        return focusService.listUserFocuses(userId, page, size)
                .map(result -> Result.success(new PageVO<>(result.getTotal(), result.getRecords())));
    }

    @GetMapping("/followers/{user_id}")
    @Operation(summary = "查询用户的所有粉丝", description = "分页查询某个用户的所有粉丝信息")
    @ApiLog("查询用户粉丝")
    public Mono<Result<PageVO<FocusUserVO>>> listUserFollowers(
            @Parameter(description = "用户ID", required = true) @PathVariable("user_id") Long userId,
            @Parameter(description = "页码", required = false) @RequestParam(defaultValue = "1") int page,
            @Parameter(description = "每页数量", required = false) @RequestParam(defaultValue = "10") int size) {
        return focusService.listUserFollowers(userId, page, size)
                .map(result -> Result.success(new PageVO<>(result.getTotal(), result.getRecords())));
    }

    @GetMapping("/count/focus/{user_id}")
    @Operation(summary = "获取用户的关注数", description = "查询用户关注的人数")
    @ApiLog("查询关注数")
    public Mono<Result<CountVO>> getFocusCount(
            @Parameter(description = "用户ID", required = true) @PathVariable("user_id") Long userId) {
        return focusService.getFocusCountByUserId(userId)
                .map(count -> Result.success(new CountVO(count)));
    }

    @GetMapping("/count/follower/{user_id}")
    @Operation(summary = "获取用户的粉丝数", description = "查询用户的粉丝数量")
    @ApiLog("查询粉丝数")
    public Mono<Result<CountVO>> getFollowerCount(
            @Parameter(description = "用户ID", required = true) @PathVariable("user_id") Long userId) {
        return focusService.getFollowerCountByUserId(userId)
                .map(count -> Result.success(new CountVO(count)));
    }
}
