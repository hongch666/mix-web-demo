package com.hcsy.spring.entity.dto;

import java.util.List;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotEmpty;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 批量ID查询DTO
 */
@Data
@AllArgsConstructor
@NoArgsConstructor
@Schema(description = "批量ID请求")
public class BatchIdsDTO {
    @Schema(description = "ID列表")
    @NotEmpty(message = "ID列表不能为空")
    private List<Long> ids;
}
