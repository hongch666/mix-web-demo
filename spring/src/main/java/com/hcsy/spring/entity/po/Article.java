package com.hcsy.spring.entity.po;

import java.time.LocalDateTime;

import org.springframework.data.annotation.Id;
import org.springframework.data.relational.core.mapping.Table;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

@Data
@Table("articles")
@Schema(description = "文章")
public class Article {
    @Schema(description = "文章ID")
    @Id
    private Long id;

    @Schema(description = "文章标题")
    private String title;

    @Schema(description = "文章内容")
    private String content;

    @Schema(description = "作者用户ID")
    private Long userId;

    @Schema(description = "标签，多个用英文逗号分隔")
    private String tags;

    @Schema(description = "状态，0草稿 1已发布")
    private Integer status;

    @Schema(description = "浏览量")
    private Integer views;

    @Schema(description = "子分类ID")
    private Integer subCategoryId;

    @Schema(description = "创建时间")
    @com.fasterxml.jackson.annotation.JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime createAt;

    @Schema(description = "更新时间")
    @com.fasterxml.jackson.annotation.JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime updateAt;
}
