package com.hcsy.spring.entity.dto;

import lombok.Data;
import jakarta.validation.constraints.*;

@Data
public class CategoryUpdateDTO {
    @NotNull(message = "分类ID不能为空")
    private Long id;
    
    @NotBlank(message = "分类名称不能为空")
    private String name;
}
