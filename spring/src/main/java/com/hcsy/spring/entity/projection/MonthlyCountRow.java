package com.hcsy.spring.entity.projection;

/**
 * 月度-文章数投影接口，用于 DATE_FORMAT 按月聚合查询结果映射
 */
public interface MonthlyCountRow {
    String getYearMonth();

    Long getCount();
}
