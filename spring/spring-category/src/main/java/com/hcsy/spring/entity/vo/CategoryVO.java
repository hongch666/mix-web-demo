package com.hcsy.spring.entity.vo;

import lombok.Data;
import java.time.LocalDateTime;
import java.util.List;

@Data
public class CategoryVO {
    private Long id;
    private String name;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
    private List<SubCategoryVO> subCategories;
}
