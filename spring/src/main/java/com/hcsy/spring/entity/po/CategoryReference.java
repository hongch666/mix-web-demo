package com.hcsy.spring.entity.po;

import org.springframework.data.annotation.Id;
import org.springframework.data.relational.core.mapping.Table;

import lombok.Data;

@Data
@Table("category_reference")
public class CategoryReference {
    @Id
    private Long id;
    private Long subCategoryId; // 子分类ID
    private String type; // 类型：link 或 pdf
    private String link; // 官网链接
    private String pdf; // PDF链接（OSS）
}
