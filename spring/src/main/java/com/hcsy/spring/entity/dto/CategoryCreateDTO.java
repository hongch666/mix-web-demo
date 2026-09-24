package com.hcsy.spring.entity.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
@Schema(description = "创建分类请求")
public class CategoryCreateDTO {
    @Schema(description = "分类名称")
    @NotBlank(message = "分类名称不能为空")
    private String name;
}
