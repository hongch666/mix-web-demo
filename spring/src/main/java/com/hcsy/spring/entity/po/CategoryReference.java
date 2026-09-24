package com.hcsy.spring.entity.po;

import org.springframework.data.annotation.Id;
import org.springframework.data.relational.core.mapping.Table;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

@Data
@Table("category_reference")
@Schema(description = "权威参考文本")
public class CategoryReference {
    @Schema(description = "参考ID")
    @Id
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
