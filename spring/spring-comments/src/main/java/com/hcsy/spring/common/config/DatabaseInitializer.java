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
            ensureTable(meta, catalog, "comments", CREATE_COMMENTS_SQL);
        } catch (Exception e) {
            logger.error("检查/创建表失败", e);
        }
    }

    private void ensureTable(DatabaseMetaData meta, String catalog, String tableName, String createSql)
            throws Exception {
        try (ResultSet rs = meta.getTables(catalog, null, tableName, new String[] { "TABLE" })) {
            if (!rs.next()) {
                jdbc.execute(createSql);
                logger.info("表 '%s' 不存在，已创建", tableName);
            } else {
                logger.debug("表 '%s' 已存在", tableName);
            }
        }
    }

    private static final String CREATE_COMMENTS_SQL = "CREATE TABLE comments (\n" +
            "    id INT NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT 'Primary Key',\n" +
            "    content VARCHAR(255) COMMENT '评论内容',\n" +
            "    star DOUBLE COMMENT '星级评分，1~10',\n" +
            "    user_id INT NOT NULL COMMENT '用户 ID',\n" +
            "    article_id INT NOT NULL COMMENT '文章 ID',\n" +
            "    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT 'Create Time',\n" +
            "    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Update Time'\n" +
            ") COMMENT=''";
}