package com.hcsy.spring.entity.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 通用数量统计响应，返回单个数量值
 */
@Data
@AllArgsConstructor
@NoArgsConstructor
@Schema(description = "数量结果")
public class CountVO {
    @Schema(description = "数量")
    private Long count;
}
