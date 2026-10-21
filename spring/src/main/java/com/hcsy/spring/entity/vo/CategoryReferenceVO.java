package com.hcsy.spring.entity.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 子分类权威参考文本响应，包含参考类型及对应的官网链接或 PDF 链接
 */
@Data
@AllArgsConstructor
@NoArgsConstructor
@Schema(description = "权威参考文本")
public class CategoryReferenceVO {
    @Schema(description = "参考ID")
    private Long id;

    @Schema(description = "子分类ID")
    private Long subCategoryId;

    @Schema(description = "类型，link 或 pdf")
    private String type;

    @Schema(description = "官网链接")
    private String link;

    @Schema(description = "PDF 链接")
    private String pdf;
}
