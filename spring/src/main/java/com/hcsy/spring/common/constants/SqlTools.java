package com.hcsy.spring.common.constants;

import java.time.Duration;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;
import java.util.regex.Pattern;

/**
 * SQL 工具常量类 — 表名白名单、只读前缀白名单、正则、查询限制等
 */
public final class SqlTools {

    private SqlTools() {
    }

    /**
     * 表名白名单：Spring 服务自管的 MySQL 业务表
     */
    public static final Set<String> TABLE_WHITELIST = new HashSet<>(Arrays.asList(
        "articles", "user", "comments", "likes", "collects", "focus",
        "category", "sub_category", "category_reference"));

    /**
     * 只读语句前缀白名单
     */
    public static final Set<String> ALLOWED_PREFIXES = new HashSet<>(Arrays.asList(
        "SELECT", "WITH", "SHOW", "DESC", "DESCRIBE", "EXPLAIN"));

    /**
     * 表名匹配正则（FROM / JOIN 后跟表名）
     */
    public static final Pattern TABLE_NAME_PATTERN = Pattern.compile(
        "\\b(?:FROM|JOIN)\\s+`?(\\w+)`?",
        Pattern.CASE_INSENSITIVE);

    /**
     * LIMIT 匹配正则
     */
    public static final Pattern LIMIT_PATTERN = Pattern.compile(
        "\\bLIMIT\\s+(\\d+)",
        Pattern.CASE_INSENSITIVE);

    /**
     * 命名参数占位符匹配正则（:paramName）
     */
    public static final Pattern NAMED_PARAM_PATTERN = Pattern.compile(
        ":\\w+");

    /**
     * 用于移除 SQL 字符串字面量，避免字符串内的 ; 被误判
     */
    public static final Pattern STRING_LITERAL_PATTERN = Pattern.compile(
        "'[^']*'|\"[^\"]*\"");

    /**
     * 用于移除末尾分号
     */
    public static final Pattern TRAILING_SEMICOLON_PATTERN = Pattern.compile(
        ";\\s*$");

    /**
     * 空白字符标准化
     */
    public static final Pattern WHITESPACE_PATTERN = Pattern.compile(
        "\\s+");

    /**
     * SQL 查询最大返回行数（LIMIT 上限）
     */
    public static final int MAX_LIMIT = 100;

    /**
     * SQL 查询超时时间
     */
    public static final Duration QUERY_TIMEOUT = Duration.ofSeconds(10);

    /**
     * 统计表行数 SQL 模板（表名来自白名单，使用反引号包裹避免保留字冲突）
     */
    public static String countRowsSql(String tableName) {
        return "SELECT COUNT(*) AS cnt FROM `" + tableName + "` LIMIT 1";
    }

    /**
     * 获取表结构 SQL 模板（表名来自白名单，使用反引号包裹避免保留字冲突）
     */
    public static String describeTableSql(String tableName) {
        return "DESCRIBE `" + tableName + "`";
    }
}
