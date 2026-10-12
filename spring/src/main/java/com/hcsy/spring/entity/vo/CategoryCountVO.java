package com.hcsy.spring.entity.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 分类计数视图对象，用于分类维度的聚合查询结果映射
 * 用具体类承载，避免接口投影（CategoryCountRow）映射不出 count 列而静默返回 null
 */
@Data
@AllArgsConstructor
@NoArgsConstructor
@Schema(description = "分类计数")
public class CategoryCountVO {
    @Schema(description = "子分类ID")
    private Integer subCategoryId;

    @Schema(description = "数量")
    private Long count;
}
