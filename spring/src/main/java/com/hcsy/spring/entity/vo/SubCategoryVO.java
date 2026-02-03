package com.hcsy.spring.entity.vo;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class SubCategoryVO {
    private Long id;
    private String name;
    private Long categoryId;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
