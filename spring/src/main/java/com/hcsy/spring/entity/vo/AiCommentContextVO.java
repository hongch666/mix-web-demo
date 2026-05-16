package com.hcsy.spring.entity.vo;

import lombok.Data;

@Data
public class AiCommentContextVO {
    private Long id;
    private String title;
    private String content;
    private String tags;
    private Long subCategoryId;
    private CategoryReferenceVO categoryReference;
}
