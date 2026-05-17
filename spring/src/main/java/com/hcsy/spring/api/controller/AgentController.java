package com.hcsy.spring.api.controller;

import java.util.Map;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.hcsy.spring.api.service.AgentService;
import com.hcsy.spring.common.utils.Constants;
import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.core.annotation.ApiLog;
import com.hcsy.spring.core.annotation.RequireInternalToken;
import com.hcsy.spring.entity.dto.AgentSqlQueryDTO;
import com.hcsy.spring.entity.vo.AgentSqlResultVO;
import com.hcsy.spring.entity.vo.AgentTableSchemaVO;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;

@RestController
@RequestMapping("/agent")
@RequiredArgsConstructor
@Tag(name = Constants.AGENT_API_TAG, description = Constants.AGENT_API_TAG_DESC)
public class AgentController {
    private final AgentService agentService;

    @GetMapping("/tables")
    @Operation(summary = Constants.AGENT_TABLES_SUMMARY, description = Constants.AGENT_TABLES_DESC)
    @RequireInternalToken
    @ApiLog(Constants.AGENT_TABLES_LOG)
    public Result getTables(@RequestParam(required = false) String name) {
        java.util.List<AgentTableSchemaVO> schemas = agentService.listTableSchemas(name);
        return Result.success(Map.of("tables", schemas));
    }

    @PostMapping("/query")
    @Operation(summary = Constants.AGENT_QUERY_SUMMARY, description = Constants.AGENT_QUERY_DESC)
    @RequireInternalToken
    @ApiLog(Constants.AGENT_QUERY_LOG)
    public Result query(@Valid @RequestBody AgentSqlQueryDTO dto) {
        AgentSqlResultVO result = agentService.query(dto);
        return Result.success(result);
    }
}
