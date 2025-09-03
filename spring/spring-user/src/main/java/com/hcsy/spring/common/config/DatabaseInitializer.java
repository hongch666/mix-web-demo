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
            ensureTable(meta, catalog, "user", CREATE_USER_SQL);
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
}