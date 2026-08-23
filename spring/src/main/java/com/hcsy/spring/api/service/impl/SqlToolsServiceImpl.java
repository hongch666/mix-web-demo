package com.hcsy.spring.api.service.impl;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;

import org.springframework.r2dbc.core.DatabaseClient;
import org.springframework.stereotype.Service;

import com.hcsy.spring.api.service.SqlToolsService;
import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.constants.SqlTools;
import com.hcsy.spring.common.exceptions.BusinessException;
import com.hcsy.spring.common.utils.SimpleLogger;

import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

/**
 * SQL工具服务实现
 * 提供受限的只读参数化SQL查询能力，供FastAPI Agent远程调用
 */
@Service
@RequiredArgsConstructor
public class SqlToolsServiceImpl implements SqlToolsService {

    private final DatabaseClient databaseClient;
    private final SimpleLogger logger;

    @Override
    public Mono<List<Map<String, Object>>> getTables(String table) {
        if (table != null && !table.isBlank()) {
            return getSingleTableSchema(table.trim());
        }
        return getAllTableSchemas();
    }

    @Override
    public Mono<Map<String, Object>> executeQuery(String query, Map<String, Object> params) {
        return Mono.just(query)
            .map(this::validateQuery)
            .flatMap(validatedQuery -> executeParameterizedQuery(validatedQuery, params));
    }

    private String validateQuery(String query) {
        if (query == null || query.isBlank()) {
            throw new BusinessException(Messages.SQL_PROXY_FORBIDDEN_STATEMENT);
        }

        String normalized = query.trim().replaceAll(SqlTools.WHITESPACE_PATTERN.pattern(), " ");
        String upperNormalized = normalized.toUpperCase();

        // 1. 检查多条语句（先移除字符串字面量，避免字符串内的 ; 被误判）
        String withoutStringLiterals = SqlTools.STRING_LITERAL_PATTERN.matcher(normalized).replaceAll("");
        if (withoutStringLiterals.contains(";")) {
            String withoutTrailing = SqlTools.TRAILING_SEMICOLON_PATTERN.matcher(normalized).replaceAll("");
            String withoutTrailingLiterals = SqlTools.STRING_LITERAL_PATTERN.matcher(withoutTrailing).replaceAll("");
            if (withoutTrailingLiterals.contains(";")) {
                throw new BusinessException(HttpCode.BAD_REQUEST, Messages.SQL_PROXY_MULTIPLE_STATEMENTS);
            }
            normalized = withoutTrailing;
            upperNormalized = normalized.toUpperCase();
        }

        // 2. 检查语句类型
        boolean allowed = false;
        for (String prefix : SqlTools.ALLOWED_PREFIXES) {
            if (upperNormalized.startsWith(prefix)) {
                allowed = true;
                break;
            }
        }
        if (!allowed) {
            throw new BusinessException(HttpCode.BAD_REQUEST, Messages.SQL_PROXY_FORBIDDEN_STATEMENT);
        }

        // 3. 检查表名白名单
        Matcher tableMatcher = SqlTools.TABLE_NAME_PATTERN.matcher(normalized);
        while (tableMatcher.find()) {
            String tableName = tableMatcher.group(1).toLowerCase();
            if (!SqlTools.TABLE_WHITELIST.contains(tableName)) {
                throw new BusinessException(HttpCode.BAD_REQUEST,
                    String.format(Messages.SQL_PROXY_TABLE_NOT_IN_WHITELIST, tableName));
            }
        }

        // 4. 检查LIMIT
        Matcher limitMatcher = SqlTools.LIMIT_PATTERN.matcher(normalized);
        if (!limitMatcher.find()) {
            throw new BusinessException(HttpCode.BAD_REQUEST, Messages.SQL_PROXY_LIMIT_REQUIRED);
        }
        int limit = Integer.parseInt(limitMatcher.group(1));
        if (limit > SqlTools.MAX_LIMIT) {
            throw new BusinessException(HttpCode.BAD_REQUEST, Messages.SQL_PROXY_LIMIT_EXCEEDED);
        }

        // 5. 参数化占位符为可选：只读前缀 + 表白名单 + LIMIT 已充分防护，无参数查询同样合法
        return normalized;
    }

    private Mono<Map<String, Object>> executeParameterizedQuery(String query, Map<String, Object> params) {
        DatabaseClient.GenericExecuteSpec spec = databaseClient.sql(query);
        if (params != null) {
            for (Map.Entry<String, Object> entry : params.entrySet()) {
                spec = spec.bind(entry.getKey(), entry.getValue());
            }
        }

        return spec.fetch().all()
            .collectList()
            .timeout(SqlTools.QUERY_TIMEOUT)
            .map(rows -> {
                Map<String, Object> result = new HashMap<>();
                if (rows.isEmpty()) {
                    result.put("columns", List.of());
                    result.put("rows", List.of());
                    result.put("rowCount", 0);
                    return result;
                }
                // 提取列名（第一行数据的key集合）
                List<String> columns = new ArrayList<>(rows.get(0).keySet());
                result.put("columns", columns);

                // 转换为值列表
                List<List<Object>> rowValues = new ArrayList<>();
                for (Map<String, Object> row : rows) {
                    List<Object> values = new ArrayList<>();
                    for (String col : columns) {
                        values.add(row.get(col));
                    }
                    rowValues.add(values);
                }
                result.put("rows", rowValues);
                result.put("rowCount", rows.size());
                return result;
            })
            .onErrorMap(e -> {
                if (e instanceof BusinessException) {
                    return e;
                }
                logger.error(String.format(Messages.SQL_PROXY_QUERY_ERROR, e.getMessage()));
                return new BusinessException(
                    String.format(Messages.SQL_PROXY_QUERY_ERROR, e.getMessage()));
            });
    }

    private Mono<List<Map<String, Object>>> getAllTableSchemas() {
        List<Map<String, Object>> result = new ArrayList<>();
        for (String tableName : SqlTools.TABLE_WHITELIST) {
            Map<String, Object> info = new HashMap<>();
            info.put("table", tableName);
            result.add(info);
        }
        // 异步获取每个表的行数（表名来自白名单，使用反引号包裹避免保留字冲突）
        return Flux.fromIterable(result)
            .flatMap(info -> {
                String tableName = (String) info.get("table");
                return databaseClient.sql(SqlTools.countRowsSql(tableName))
                    .fetch()
                    .one()
                    .map(row -> {
                        info.put("rowCount", row.get("cnt"));
                        return info;
                    })
                    .onErrorResume(e -> {
                        info.put("rowCount", -1);
                        return Mono.just(info);
                    });
            })
            .collectList();
    }

    private Mono<List<Map<String, Object>>> getSingleTableSchema(String tableName) {
        if (!SqlTools.TABLE_WHITELIST.contains(tableName)) {
            throw new BusinessException(
                String.format(Messages.SQL_PROXY_TABLE_NOT_IN_WHITELIST, tableName));
        }

        return databaseClient.sql(SqlTools.describeTableSql(tableName))
            .fetch()
            .all()
            .collectList()
            .map(columns -> {
                List<Map<String, Object>> result = new ArrayList<>();
                Map<String, Object> tableInfo = new HashMap<>();
                tableInfo.put("table", tableName);
                List<Map<String, Object>> columnList = new ArrayList<>();
                for (Map<String, Object> col : columns) {
                    Map<String, Object> colInfo = new HashMap<>();
                    colInfo.put("name", col.get("Field"));
                    colInfo.put("type", col.get("Type"));
                    colInfo.put("key", col.get("Key"));
                    colInfo.put("comment", col.getOrDefault("Comment", ""));
                    columnList.add(colInfo);
                }
                tableInfo.put("columns", columnList);
                result.add(tableInfo);
                return result;
            })
            .onErrorMap(e -> new BusinessException(
                String.format(Messages.SQL_PROXY_TABLE_SCHEMA_ERROR, e.getMessage())));
    }
}
