package com.hcsy.spring.entity.vo;

import java.time.LocalDateTime;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class ArticleWithCategoryVO {
    private Long id;
    private String title;
    private String content;
    private Long userId;
    private String username;
    private String tags;
    private Integer status;
    private Integer views;
    private Integer subCategoryId;
    private String subCategoryName;
    private Long categoryId;
    private String categoryName;
    private LocalDateTime createAt;
    private LocalDateTime updateAt;
}
