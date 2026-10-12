package com.hcsy.spring.entity.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 月度计数视图对象，用于按月维度的聚合查询结果映射
 * 用具体类承载，避免接口投影（MonthlyCountRow）映射不出 count 列而静默返回 null
 */
@Data
@AllArgsConstructor
@NoArgsConstructor
@Schema(description = "月度计数")
public class MonthlyCountVO {
    @Schema(description = "年月，格式 yyyy-MM")
    private String yearMonth;

    @Schema(description = "数量")
    private Long count;
}
