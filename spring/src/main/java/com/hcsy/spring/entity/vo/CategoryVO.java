package com.hcsy.spring.entity.vo;

import java.time.LocalDateTime;
import java.util.List;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 父分类响应，包含分类名称、创建与更新时间及其下的子分类列表
 */
@Data
@AllArgsConstructor
@NoArgsConstructor
@Schema(description = "分类")
public class CategoryVO {
    @Schema(description = "分类ID")
    private Long id;

    @Schema(description = "分类名称")
    private String name;

    @Schema(description = "创建时间")
    private LocalDateTime createTime;

    @Schema(description = "更新时间")
    private LocalDateTime updateTime;

    @Schema(description = "子分类列表")
    private List<SubCategoryVO> subCategories;
}
