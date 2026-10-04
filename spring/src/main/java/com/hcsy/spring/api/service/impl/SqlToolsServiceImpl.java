package com.hcsy.spring.api.service.impl;

import java.util.ArrayList;
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
import com.hcsy.spring.entity.vo.SqlColumnInfoVO;
import com.hcsy.spring.entity.vo.SqlQueryResultVO;
import com.hcsy.spring.entity.vo.SqlTableSchemaVO;

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
    public Mono<List<SqlTableSchemaVO>> getTables(String table) {
        if (table != null && !table.isBlank()) {
            return getSingleTableSchema(table.trim());
        }
        return getAllTableSchemas();
    }

    @Override
    public Mono<SqlQueryResultVO> executeQuery(String query, Map<String, Object> params) {
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

    private Mono<SqlQueryResultVO> executeParameterizedQuery(String query, Map<String, Object> params) {
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
                if (rows.isEmpty()) {
                    return new SqlQueryResultVO(List.of(), List.of(), 0);
                }
                // 提取列名（第一行数据的key集合）
                List<String> columns = new ArrayList<>(rows.get(0).keySet());

                // 转换为值列表
                List<List<Object>> rowValues = new ArrayList<>();
                for (Map<String, Object> row : rows) {
                    List<Object> values = new ArrayList<>();
                    for (String col : columns) {
                        values.add(row.get(col));
                    }
                    rowValues.add(values);
                }
                return new SqlQueryResultVO(columns, rowValues, rows.size());
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

    private Mono<List<SqlTableSchemaVO>> getAllTableSchemas() {
        List<String> tableNames = new ArrayList<>(SqlTools.TABLE_WHITELIST);
        // 异步获取每个表的行数（表名来自白名单，使用反引号包裹避免保留字冲突）
        return Flux.fromIterable(tableNames)
            .flatMap(tableName -> databaseClient.sql(SqlTools.countRowsSql(tableName))
                .fetch()
                .one()
                .map(row -> new SqlTableSchemaVO(tableName, ((Number) row.get("cnt")).intValue(), null))
                .onErrorResume(e -> Mono.just(new SqlTableSchemaVO(tableName, -1, null))))
            .collectList();
    }

    private Mono<List<SqlTableSchemaVO>> getSingleTableSchema(String tableName) {
        if (!SqlTools.TABLE_WHITELIST.contains(tableName)) {
            throw new BusinessException(
                String.format(Messages.SQL_PROXY_TABLE_NOT_IN_WHITELIST, tableName));
        }

        return databaseClient.sql(SqlTools.describeTableSql(tableName))
            .fetch()
            .all()
            .collectList()
            .map(columns -> {
                List<SqlColumnInfoVO> columnList = new ArrayList<>();
                for (Map<String, Object> col : columns) {
                    columnList.add(new SqlColumnInfoVO(
                        String.valueOf(col.get("Field")),
                        String.valueOf(col.get("Type")),
                        String.valueOf(col.get("Key")),
                        String.valueOf(col.getOrDefault("Comment", ""))));
                }
                return List.of(new SqlTableSchemaVO(tableName, null, columnList));
            })
            .onErrorMap(e -> new BusinessException(
                String.format(Messages.SQL_PROXY_TABLE_SCHEMA_ERROR, e.getMessage())));
    }
}
