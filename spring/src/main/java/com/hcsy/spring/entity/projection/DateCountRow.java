package com.hcsy.spring.entity.projection;

import java.time.LocalDate;

/**
 * 日期-计数投影接口，用于 GROUP BY DATE 的聚合查询结果映射
 */
public interface DateCountRow {
    LocalDate getDate();

    Long getCount();
}
