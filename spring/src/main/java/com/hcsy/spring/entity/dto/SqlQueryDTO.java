package com.hcsy.spring.entity.dto;

import java.util.Map;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 只读SQL查询请求DTO
 */
@Data
@AllArgsConstructor
@NoArgsConstructor
@Schema(description = "只读 SQL 查询请求")
public class SqlQueryDTO {
    @Schema(description = "只读 SELECT 语句，使用 :param 占位")
    @NotBlank(message = "SQL查询语句不能为空")
    private String query;

    @Schema(description = "命名参数")
    private Map<String, Object> params;
}
