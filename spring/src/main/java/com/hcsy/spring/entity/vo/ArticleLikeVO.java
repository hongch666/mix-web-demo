package com.hcsy.spring.entity.vo;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class ArticleLikeVO {
    private Long id; // 点赞ID
    private Long articleId;
    private String title;
    private String content;
    private Long userId;
    private String authorName; // 文章作者名称（新增）
    private String tags;
    private Integer status;
    private Integer views;
    private Integer subCategoryId;
    private String categoryName; // 父分类名称（新增）
    private String subCategoryName; // 子分类名称（新增）
    private LocalDateTime articleCreateAt;
    private LocalDateTime articleUpdateAt;
    private LocalDateTime likedTime; // 点赞时间
}
