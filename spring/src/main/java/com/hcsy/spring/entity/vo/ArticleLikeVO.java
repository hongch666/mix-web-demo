package com.hcsy.spring.entity.vo;

import java.time.LocalDateTime;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
@Schema(description = "文章点赞视图")
public class ArticleLikeVO {
    @Schema(description = "点赞ID")
    private Long id;

    @Schema(description = "文章ID")
    private Long articleId;

    @Schema(description = "文章标题")
    private String title;

    @Schema(description = "文章内容")
    private String content;

    @Schema(description = "作者用户ID")
    private Long userId;

    @Schema(description = "作者名称")
    private String authorName;

    @Schema(description = "标签，多个用英文逗号分隔")
    private String tags;

    @Schema(description = "状态，0草稿 1已发布")
    private Integer status;

    @Schema(description = "浏览量")
    private Integer views;

    @Schema(description = "子分类ID")
    private Integer subCategoryId;

    @Schema(description = "父分类名称")
    private String categoryName;

    @Schema(description = "子分类名称")
    private String subCategoryName;

    @Schema(description = "文章创建时间")
    private LocalDateTime articleCreateAt;

    @Schema(description = "文章更新时间")
    private LocalDateTime articleUpdateAt;

    @Schema(description = "点赞时间")
    private LocalDateTime likedTime;
}
