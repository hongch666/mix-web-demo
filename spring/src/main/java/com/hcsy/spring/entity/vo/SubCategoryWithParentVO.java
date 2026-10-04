package com.hcsy.spring.entity.vo;

import java.time.LocalDateTime;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 子分类及其父分类信息视图对象
 * 用于内部服务查询子分类层级信息
 */
@Data
@AllArgsConstructor
@NoArgsConstructor
@Schema(description = "子分类及父分类信息")
@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
public class SubCategoryWithParentVO {

    @Schema(description = "子分类ID")
    private Long id;

    @Schema(description = "子分类名称")
    private String name;

    @Schema(description = "所属分类ID")
    private Long categoryId;

    @Schema(description = "所属分类名称")
    private String categoryName;

    @Schema(description = "创建时间")
    private LocalDateTime createTime;

    @Schema(description = "更新时间")
    private LocalDateTime updateTime;
}
