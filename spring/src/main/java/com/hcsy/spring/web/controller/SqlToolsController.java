package com.hcsy.spring.web.controller;

import java.util.List;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.hcsy.spring.application.service.SqlToolsService;
import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.entity.dto.SqlQueryDTO;
import com.hcsy.spring.entity.vo.SqlQueryResultVO;
import com.hcsy.spring.entity.vo.SqlTableSchemaVO;
import com.hcsy.spring.web.logging.annotation.ApiLog;
import com.hcsy.spring.web.security.annotation.RequireInternalToken;

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

    /**
     * GET /sql-tools/tables 内部接口，返回白名单内MySQL表的结构信息，可通过 table 参数限定单个表
     */
    @GetMapping("/tables")
    @Operation(summary = "获取表结构信息（内部）", description = "获取白名单内MySQL表的结构信息，供FastAPI Agent远程调用")
    @RequireInternalToken
    @ApiLog("内部获取表结构信息")
    public Mono<Result<List<SqlTableSchemaVO>>> getTables(
        @RequestParam(required = false) String table) {
        return sqlToolsService.getTables(table).map(Result::success);
    }

    /**
     * POST /sql-tools/query 内部接口，执行经过校验与白名单限制的只读参数化SQL查询并返回结果集
     */
    @PostMapping("/query")
    @Operation(summary = "执行只读SQL查询（内部）", description = "执行受限的只读参数化SQL查询，供FastAPI Agent远程调用")
    @RequireInternalToken
    @ApiLog("内部执行SQL查询")
    public Mono<Result<SqlQueryResultVO>> executeQuery(
        @Valid @RequestBody SqlQueryDTO dto) {
        return sqlToolsService.executeQuery(dto.getQuery(), dto.getParams())
            .map(Result::success);
    }
}
