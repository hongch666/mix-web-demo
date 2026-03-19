package com.hcsy.spring.entity.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

@Data
public class SubCategoryCreateDTO {
    @NotBlank(message = "子分类名称不能为空")
    private String name;

    @NotNull(message = "父分类ID不能为空")
    private Long categoryId;
}
