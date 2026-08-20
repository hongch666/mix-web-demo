package com.hcsy.spring.entity.projection;

import java.time.LocalDateTime;

/**
 * 文章 Excel 导出投影接口，用于多表 JOIN 查询结果映射
 */
public interface ArticleExcelRow {
    Long getId();

    String getTitle();

    String getContent();

    Long getUser_id();

    String getUsername();

    String getTags();

    Integer getStatus();

    LocalDateTime getCreate_at();

    LocalDateTime getUpdate_at();

    Integer getViews();

    Integer getSub_category_id();

    String getSub_category_name();

    Long getCategory_id();

    String getCategory_name();

    Long getLike_count();

    Long getCollect_count();
}
