package com.hcsy.spring.entity.vo;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 子分类文章数量统计视图对象
 */
@Data
@AllArgsConstructor
@NoArgsConstructor
@Schema(description = "子分类文章数量统计")
@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
public class CategoryArticleCountVO {

    @Schema(description = "子分类ID")
    private Integer subCategoryId;

    @Schema(description = "该子分类下的文章数量")
    private Long count;
}
