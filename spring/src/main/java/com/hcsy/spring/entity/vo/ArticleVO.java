package com.hcsy.spring.entity.vo;

import lombok.Data;

@Data
public class ArticleVO {
    private Long id;
    private String title;
    private String content;
    private Long userId;
    private String tags;
    private Integer status;
    private Integer views;
    private Integer subCategoryId;
    private String createAt;
    private String updateAt;
}
