package com.hcsy.spring.entity.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import lombok.Data;

@Data
@Schema(description = "创建权威参考文本请求")
public class CategoryReferenceCreateDTO {
    @Schema(description = "子分类ID")
    @NotNull(message = "子分类ID不能为空")
    private Long subCategoryId;

    @Schema(description = "类型，link 或 pdf")
    @NotBlank(message = "类型不能为空，必须为 link 或 pdf")
    @Pattern(regexp = "^(link|pdf)$", message = "类型只能为 link 或 pdf")
    private String type;

    @Schema(description = "官网链接，类型为 link 时必填")
    @Size(max = 255, message = "链接长度不能超过255个字符")
    private String link; // 当type为link时，此字段必填

    @Schema(description = "PDF 链接，类型为 pdf 时必填")
    @Size(max = 255, message = "PDF链接长度不能超过255个字符")
    private String pdf; // 当type为pdf时，此字段必填
}
