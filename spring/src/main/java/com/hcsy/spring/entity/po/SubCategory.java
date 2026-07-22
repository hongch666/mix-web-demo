package com.hcsy.spring.entity.po;

import java.time.LocalDateTime;

import org.springframework.data.annotation.Id;
import org.springframework.data.relational.core.mapping.Table;

import lombok.Data;

@Data
@Table("sub_category")
public class SubCategory {
    @Id
    private Long id;
    private String name;
    private Long categoryId; // 关联的主分类ID
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
