package com.hcsy.spring.entity.po;

import java.time.LocalDateTime;

import org.springframework.data.annotation.Id;
import org.springframework.data.relational.core.mapping.Table;

import lombok.Data;

@Data
@Table("articles")
public class Article {
    @Id
    private Long id;
    private String title;
    private String content;
    private Long userId;
    private String tags; // 标签用逗号分隔
    private Integer status; // 0=草稿，1=已发布
    private Integer views; // 浏览量
    private Integer subCategoryId; // 子分类ID
    private LocalDateTime createAt;
    private LocalDateTime updateAt;
}
