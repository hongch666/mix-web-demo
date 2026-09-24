package com.hcsy.spring.entity.vo;

import java.time.LocalDateTime;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
@Schema(description = "带分类的文章")
public class ArticleWithCategoryVO {
    @Schema(description = "文章ID")
    private Long id;

    @Schema(description = "文章标题")
    private String title;

    @Schema(description = "文章内容")
    private String content;

    @Schema(description = "作者用户ID")
    private Long userId;

    @Schema(description = "作者名称")
    private String username;

    @Schema(description = "标签，多个用英文逗号分隔")
    private String tags;

    @Schema(description = "状态，0草稿 1已发布")
    private Integer status;

    @Schema(description = "浏览量")
    private Integer views;

    @Schema(description = "子分类ID")
    private Integer subCategoryId;

    @Schema(description = "子分类名称")
    private String subCategoryName;

    @Schema(description = "父分类ID")
    private Long categoryId;

    @Schema(description = "父分类名称")
    private String categoryName;

    @Schema(description = "创建时间")
    private LocalDateTime createAt;

    @Schema(description = "更新时间")
    private LocalDateTime updateAt;
}
