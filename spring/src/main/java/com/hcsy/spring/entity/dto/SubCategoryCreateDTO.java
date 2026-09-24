package com.hcsy.spring.entity.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

@Data
@Schema(description = "创建子分类请求")
public class SubCategoryCreateDTO {
    @Schema(description = "子分类名称")
    @NotBlank(message = "子分类名称不能为空")
    private String name;

    @Schema(description = "父分类ID")
    @NotNull(message = "父分类ID不能为空")
    private Long categoryId;
}
