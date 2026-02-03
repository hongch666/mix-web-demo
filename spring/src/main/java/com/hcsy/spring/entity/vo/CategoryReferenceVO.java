package com.hcsy.spring.entity.vo;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class CategoryReferenceVO {
    private Long id;
    private Long subCategoryId;
    private String type; // link 或 pdf
    private String link;
    private String pdf;
}
