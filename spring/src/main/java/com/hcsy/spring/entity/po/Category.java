package com.hcsy.spring.entity.po;

import java.time.LocalDateTime;

import org.springframework.data.annotation.Id;
import org.springframework.data.relational.core.mapping.Table;

import lombok.Data;

@Data
@Table("category")
public class Category {
    @Id
    private Long id;
    private String name;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
