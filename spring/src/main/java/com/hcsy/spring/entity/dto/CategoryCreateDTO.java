package com.hcsy.spring.entity.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class CategoryCreateDTO {
    @NotBlank(message = "分类名称不能为空")
    private String name;
}
