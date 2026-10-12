package com.hcsy.spring.entity.vo;

import java.time.LocalDate;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 日期-计数视图对象，用于 GROUP BY DATE 的聚合查询结果映射
 * 用具体类承载，避免接口投影（DateCountRow）映射不出 count 列而静默返回 null
 */
@Data
@AllArgsConstructor
@NoArgsConstructor
@Schema(description = "日期与计数")
public class DateCountVO {
    @Schema(description = "日期")
    private LocalDate date;

    @Schema(description = "数量")
    private Long count;
}
