package com.hcsy.spring.common.config;

import lombok.RequiredArgsConstructor;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;

import com.hcsy.spring.common.utils.SimpleLogger;

import javax.sql.DataSource;
import java.sql.DatabaseMetaData;
import java.sql.ResultSet;
import java.sql.Connection;

@Component
@RequiredArgsConstructor
public class DatabaseInitializer implements ApplicationRunner {

    private final DataSource dataSource;
    private final JdbcTemplate jdbc;
    private final SimpleLogger logger;

    @Override
    public void run(ApplicationArguments args) {
        try (Connection conn = dataSource.getConnection()) {
            DatabaseMetaData meta = conn.getMetaData();
            String catalog = conn.getCatalog(); // MySQL: 数据库名
            // 建表顺序：category -> sub_category -> user -> articles
            ensureTable(meta, catalog, "category", CREATE_CATEGORY_SQL);
            ensureTable(meta, catalog, "sub_category", CREATE_SUBCATEGORY_SQL);
            ensureTable(meta, catalog, "user", CREATE_USER_SQL);
            ensureTable(meta, catalog, "articles", CREATE_ARTICLES_SQL);
        } catch (Exception e) {
            logger.error("检查/创建表失败", e);
        }
    }

    private void ensureTable(DatabaseMetaData meta, String catalog, String tableName, String createSql)
            throws Exception {
        try (ResultSet rs = meta.getTables(catalog, null, tableName, new String[] { "TABLE" })) {
            if (!rs.next()) {
                jdbc.execute(createSql);
                logger.info("表 '{}' 不存在，已创建", tableName);
            } else {
                logger.debug("表 '{}' 已存在", tableName);
            }
        }
    }

    private static final String CREATE_USER_SQL = "CREATE TABLE user (\n" +
            "    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '用户ID',\n" +
            "    name VARCHAR(255) NOT NULL UNIQUE COMMENT '用户名',\n" +
            "    password VARCHAR(255) NOT NULL COMMENT '密码',\n" +
            "    email VARCHAR(255) UNIQUE COMMENT '邮箱',\n" +
            "    age INT COMMENT '年龄',\n" +
            "    role VARCHAR(255) NOT NULL COMMENT '用户权限',\n" +
            "    img VARCHAR(255) COMMENT '用户头像'\n" +
            ") COMMENT='用户表'";

    private static final String CREATE_ARTICLES_SQL = "CREATE TABLE articles (\n" +
            "    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '用户ID',\n" +
            "    title VARCHAR(255) NOT NULL UNIQUE COMMENT '用户名',\n" +
            "    content TEXT NOT NULL COMMENT '文章内容',\n" +
            "    user_id BIGINT NOT NULL COMMENT '用户id',\n" +
            "    sub_category_id BIGINT NOT NULL COMMENT '子分类id',\n" +
            "    tags VARCHAR(255) NOT NULL COMMENT '文章标签',\n" +
            "    status INT NOT NULL COMMENT '文章状态',\n" +
            "    views INT NOT NULL COMMENT '文章浏览量',\n" +
            "    create_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',\n" +
            "    update_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'\n" +
            ") COMMENT='文章表'";

    private static final String CREATE_CATEGORY_SQL = "CREATE TABLE category (\n" +
            "    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键',\n" +
            "    name VARCHAR(255) NOT NULL COMMENT '分类名称',\n" +
            "    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',\n" +
            "    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'\n" +
            ") COMMENT='分类表'";

    private static final String CREATE_SUBCATEGORY_SQL = "CREATE TABLE sub_category (\n" +
            "    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键',\n" +
            "    name VARCHAR(255) NOT NULL COMMENT '子分类名称',\n" +
            "    category_id BIGINT NOT NULL COMMENT '所属分类ID',\n" +
            "    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',\n" +
            "    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',\n" +
            "    FOREIGN KEY (category_id) REFERENCES category(id) ON DELETE CASCADE\n" +
            ") COMMENT='子分类表'";
}