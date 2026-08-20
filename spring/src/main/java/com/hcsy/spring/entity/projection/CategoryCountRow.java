package com.hcsy.spring.entity.projection;

/**
 * 分类-文章数投影接口，用于 GROUP BY sub_category_id 聚合查询结果映射
 */
public interface CategoryCountRow {
    Integer getSubCategoryId();

    Long getCount();
}
