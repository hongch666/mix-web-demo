package com.hcsy.spring.entity.dto;

import java.util.Map;

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
public class SqlQueryDTO {
    @NotBlank(message = "SQL查询语句不能为空")
    private String query;

    private Map<String, Object> params;
}