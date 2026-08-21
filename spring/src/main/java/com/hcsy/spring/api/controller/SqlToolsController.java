package com.hcsy.spring.api.controller;

import java.util.List;
import java.util.Map;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.hcsy.spring.api.service.SqlToolsService;
import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.core.annotation.ApiLog;
import com.hcsy.spring.core.annotation.RequireInternalToken;
import com.hcsy.spring.entity.dto.SqlQueryDTO;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;

/**
 * SQL工具接口（供FastAPI Agent远程调用）
 * 提供受限的只读参数化SQL查询能力，表名白名单控制
 */
@RestController
@RequestMapping("/sql-tools")
@RequiredArgsConstructor
@Tag(name = "SQL工具", description = "供FastAPI Agent远程调用的SQL工具接口")
public class SqlToolsController {

    private final SqlToolsService sqlToolsService;

    @GetMapping("/tables")
    @Operation(summary = "获取表结构信息（内部）", description = "获取白名单内MySQL表的结构信息，供FastAPI Agent远程调用")
    @RequireInternalToken
    @ApiLog("内部获取表结构信息")
    public Mono<Result<List<Map<String, Object>>>> getTables(
        @RequestParam(required = false) String table) {
        return sqlToolsService.getTables(table).map(Result::success);
    }

    @PostMapping("/query")
    @Operation(summary = "执行只读SQL查询（内部）", description = "执行受限的只读参数化SQL查询，供FastAPI Agent远程调用")
    @RequireInternalToken
    @ApiLog("内部执行SQL查询")
    public Mono<Result<Map<String, Object>>> executeQuery(
        @Valid @RequestBody SqlQueryDTO dto) {
        return sqlToolsService.executeQuery(dto.getQuery(), dto.getParams())
            .map(Result::success);
    }
}
