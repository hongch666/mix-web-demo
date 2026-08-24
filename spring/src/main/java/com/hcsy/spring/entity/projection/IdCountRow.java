package com.hcsy.spring.entity.projection;

/**
 * ID-计数投影接口，用于批量统计的聚合查询结果映射。
 * 对应 SQL 中的 SELECT <id 列> AS id, COUNT(*) AS count。
 */
public interface IdCountRow {
    Long getId();

    Long getCount();
}
