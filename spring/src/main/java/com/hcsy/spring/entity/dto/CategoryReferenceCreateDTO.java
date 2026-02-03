package com.hcsy.spring.entity.dto;

import lombok.Data;
import jakarta.validation.constraints.*;

@Data
public class CategoryReferenceCreateDTO {
    @NotNull(message = "子分类ID不能为空")
    private Long subCategoryId;

    @NotBlank(message = "类型不能为空，必须为 link 或 pdf")
    @Pattern(regexp = "^(link|pdf)$", message = "类型只能为 link 或 pdf")
    private String type;

    private String link; // 当type为link时，此字段必填
    
    private String pdf; // 当type为pdf时，此字段必填
}
