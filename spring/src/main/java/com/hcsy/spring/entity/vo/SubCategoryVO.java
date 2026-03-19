package com.hcsy.spring.entity.vo;

import java.time.LocalDateTime;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

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
