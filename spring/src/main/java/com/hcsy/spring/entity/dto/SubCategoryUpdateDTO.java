package com.hcsy.spring.entity.dto;

import lombok.Data;
import jakarta.validation.constraints.*;

@Data
public class SubCategoryUpdateDTO {
    @NotNull(message = "子分类ID不能为空")
    private Long id;

    @NotBlank(message = "子分类名称不能为空")
    private String name;
    
    @NotNull(message = "父分类ID不能为空")
    private Long categoryId;
}
