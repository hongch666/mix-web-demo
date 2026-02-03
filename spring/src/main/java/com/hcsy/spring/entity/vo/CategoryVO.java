package com.hcsy.spring.entity.vo;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.List;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class CategoryVO {
    private Long id;
    private String name;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
    private List<SubCategoryVO> subCategories;
}
