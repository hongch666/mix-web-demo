package com.hcsy.spring.entity.vo;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 月度文章发布数量统计视图对象
 */
@Data
@AllArgsConstructor
@NoArgsConstructor
@Schema(description = "月度文章发布数量统计")
@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
public class MonthlyPublishCountVO {

    @Schema(description = "年月，格式 yyyy-MM")
    private String yearMonth;

    @Schema(description = "该月发布文章数量")
    private Long count;
}
