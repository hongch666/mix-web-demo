package com.hcsy.spring.entity.projection;

import java.time.LocalDateTime;

/**
 * 文章 Excel 导出投影接口，用于多表 JOIN 查询结果映射
 */
public interface ArticleExcelRow {
    /**
     * 返回文章 ID
     */
    Long getId();

    /**
     * 返回文章标题
     */
    String getTitle();

    /**
     * 返回文章内容
     */
    String getContent();

    /**
     * 返回文章作者用户 ID
     */
    Long getUser_id();

    /**
     * 返回文章作者用户名
     */
    String getUsername();

    /**
     * 返回文章标签
     */
    String getTags();

    /**
     * 返回文章发布状态
     */
    Integer getStatus();

    /**
     * 返回文章创建时间
     */
    LocalDateTime getCreate_at();

    /**
     * 返回文章更新时间
     */
    LocalDateTime getUpdate_at();

    /**
     * 返回文章浏览量
     */
    Integer getViews();

    /**
     * 返回文章所属子分类 ID
     */
    Integer getSub_category_id();

    /**
     * 返回文章所属子分类名称
     */
    String getSub_category_name();

    /**
     * 返回文章所属分类 ID
     */
    Long getCategory_id();

    /**
     * 返回文章所属分类名称
     */
    String getCategory_name();

    /**
     * 返回文章点赞数
     */
    Long getLike_count();

    /**
     * 返回文章收藏数
     */
    Long getCollect_count();
}
