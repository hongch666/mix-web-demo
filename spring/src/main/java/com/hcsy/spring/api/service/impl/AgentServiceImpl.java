package com.hcsy.spring.api.service.impl;

import java.sql.ResultSetMetaData;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.LocalTime;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

import com.hcsy.spring.api.service.AgentService;
import com.hcsy.spring.common.exceptions.BusinessException;
import com.hcsy.spring.common.utils.Constants;
import com.hcsy.spring.common.utils.HttpCode;
import com.hcsy.spring.entity.dto.AgentSqlQueryDTO;
import com.hcsy.spring.entity.vo.AgentColumnVO;
import com.hcsy.spring.entity.vo.AgentIndexVO;
import com.hcsy.spring.entity.vo.AgentSqlResultVO;
import com.hcsy.spring.entity.vo.AgentTableSchemaVO;

import lombok.RequiredArgsConstructor;

@Service
@RequiredArgsConstructor
public class AgentServiceImpl implements AgentService {
    private static final Set<String> ALLOWED_TABLES = Set.of(
            "articles", "user", "category", "sub_category", "comments", "likes", "collects", "focus",
            "category_reference");
    private static final Set<String> READONLY_PREFIXES = Set.of("SELECT", "WITH", "SHOW", "DESC", "DESCRIBE",
            "EXPLAIN");
    private static final Pattern TABLE_PATTERN = Pattern.compile(
            "\\b(?:FROM|JOIN|UPDATE|INTO|TABLE|DESC|DESCRIBE)\\s+`?([a-zA-Z_][a-zA-Z0-9_]*)`?",
            Pattern.CASE_INSENSITIVE);
    private static final int MAX_ROWS = 500;

    private final JdbcTemplate jdbcTemplate;

    @Override
    public List<AgentTableSchemaVO> listTableSchemas(String name) {
        String tableName = normalizeTableName(name);
        if (tableName != null && !ALLOWED_TABLES.contains(tableName)) {
            return Collections.emptyList();
        }

        List<String> tables = tableName == null ? new ArrayList<>(ALLOWED_TABLES) : List.of(tableName);
        return tables.stream()
                .map(this::buildTableSchema)
                .toList();
    }

    @SuppressWarnings("null")
    @Override
    public AgentSqlResultVO query(AgentSqlQueryDTO dto) {
        String sql = dto.getSql() == null ? "" : dto.getSql().trim();
        String validationError = validateSql(sql);
        if (validationError != null) {
            throw new BusinessException(HttpCode.BAD_REQUEST, validationError);
        }

        try {
            String executableSql = appendLimitIfNeeded(sql);
            return jdbcTemplate.query(executableSql, rs -> {
                ResultSetMetaData metaData = rs.getMetaData();
                int columnCount = metaData.getColumnCount();
                List<String> columns = new ArrayList<>();
                for (int i = 1; i <= columnCount; i++) {
                    columns.add(metaData.getColumnLabel(i));
                }

                List<List<Object>> rows = new ArrayList<>();
                while (rs.next() && rows.size() < MAX_ROWS) {
                    List<Object> row = new ArrayList<>();
                    for (int i = 1; i <= columnCount; i++) {
                        row.add(formatValue(rs.getObject(i)));
                    }
                    rows.add(row);
                }
                return new AgentSqlResultVO(columns, rows, rows.size());
            });
        } catch (BusinessException e) {
            throw e;
        } catch (Exception e) {
            throw new BusinessException(HttpCode.BAD_REQUEST, e.getMessage());
        }
    }

    private AgentTableSchemaVO buildTableSchema(String tableName) {
        List<AgentColumnVO> columns = jdbcTemplate.query("""
                SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_DEFAULT
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = ?
                ORDER BY ORDINAL_POSITION
                """, (rs, rowNum) -> new AgentColumnVO(
                rs.getString("COLUMN_NAME"),
                rs.getString("COLUMN_TYPE"),
                "YES".equalsIgnoreCase(rs.getString("IS_NULLABLE")),
                rs.getString("COLUMN_DEFAULT")), tableName);

        List<String> primaryKey = jdbcTemplate.query("""
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = ? AND CONSTRAINT_NAME = 'PRIMARY'
                ORDER BY ORDINAL_POSITION
                """, (rs, rowNum) -> rs.getString("COLUMN_NAME"), tableName);

        Map<String, List<String>> indexMap = new LinkedHashMap<>();
        jdbcTemplate.query("""
                SELECT INDEX_NAME, COLUMN_NAME
                FROM INFORMATION_SCHEMA.STATISTICS
                WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = ?
                ORDER BY INDEX_NAME, SEQ_IN_INDEX
                """, rs -> {
            String indexName = rs.getString("INDEX_NAME");
            indexMap.computeIfAbsent(indexName, key -> new ArrayList<>()).add(rs.getString("COLUMN_NAME"));
        }, tableName);
        List<AgentIndexVO> indexes = indexMap.entrySet().stream()
                .map(entry -> new AgentIndexVO(entry.getKey(), entry.getValue()))
                .toList();

        return new AgentTableSchemaVO(tableName, columns, primaryKey, indexes);
    }

    private String validateSql(String sql) {
        String normalized = sql.replaceAll("\\s+", " ").trim();
        if (normalized.isEmpty()) {
            return Constants.AGENT_SQL_REQUIRED;
        }
        String withoutTrailingSemicolon = normalized.replaceAll(";+$", "").trim();
        if (withoutTrailingSemicolon.contains(";")) {
            return Constants.AGENT_SQL_SINGLE_READONLY;
        }

        String upper = withoutTrailingSemicolon.toUpperCase(Locale.ROOT);
        if (READONLY_PREFIXES.stream().noneMatch(upper::startsWith)) {
            return Constants.AGENT_SQL_READONLY_ONLY;
        }

        Set<String> tables = extractTables(withoutTrailingSemicolon);
        if (tables.isEmpty() && !isQueryWithoutTableAllowed(upper)) {
            return Constants.AGENT_SQL_TABLE_SCOPE_REQUIRED;
        }
        if (!tables.isEmpty() && !ALLOWED_TABLES.containsAll(tables)) {
            return Constants.AGENT_SQL_TABLE_SCOPE_INVALID_PREFIX + tables;
        }
        return null;
    }

    private boolean isQueryWithoutTableAllowed(String upperSql) {
        return upperSql.startsWith("SELECT")
                || upperSql.startsWith("WITH")
                || upperSql.startsWith("EXPLAIN SELECT")
                || upperSql.startsWith("EXPLAIN WITH");
    }

    private Set<String> extractTables(String sql) {
        Matcher matcher = TABLE_PATTERN.matcher(sql);
        Set<String> tables = new LinkedHashSet<>();
        while (matcher.find()) {
            tables.add(normalizeTableName(matcher.group(1)));
        }
        return tables;
    }

    private String normalizeTableName(String name) {
        if (name == null || name.isBlank()) {
            return null;
        }
        String tableName = name.trim().replace("`", "").toLowerCase(Locale.ROOT);
        if ("users".equals(tableName)) {
            return "user";
        }
        return tableName;
    }

    private String appendLimitIfNeeded(String sql) {
        String normalized = sql.trim().replaceAll(";+$", "");
        String upper = normalized.toUpperCase(Locale.ROOT);
        if (upper.startsWith("SELECT") || upper.startsWith("WITH")) {
            if (!Pattern.compile("\\bLIMIT\\b", Pattern.CASE_INSENSITIVE).matcher(normalized).find()) {
                return normalized + " LIMIT " + MAX_ROWS;
            }
        }
        return normalized;
    }

    private Object formatValue(Object value) {
        if (value instanceof LocalDateTime || value instanceof LocalDate || value instanceof LocalTime) {
            return value.toString();
        }
        if (value instanceof byte[] bytes) {
            return Arrays.toString(bytes);
        }
        return value;
    }
}
