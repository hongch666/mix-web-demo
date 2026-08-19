package com.hcsy.spring.entity.dto;

import java.util.List;

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
public class BatchIdsDTO {
    @NotEmpty(message = "ID列表不能为空")
    private List<Long> ids;
}
