package com.hcsy.spring.entity.vo;

import lombok.Data;

@Data
public class CategoryReferenceVO {
    private Long id;
    private Long subCategoryId;
    private String type; // link 或 pdf
    private String link;
    private String pdf;
}
