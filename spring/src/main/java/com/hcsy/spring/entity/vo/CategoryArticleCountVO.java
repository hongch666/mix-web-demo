package com.hcsy.spring.entity.vo;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class CategoryArticleCountVO {
    private Long categoryId;
    private String categoryName;
    private Long articleCount;
}
