package com.hcsy.spring.vo;

import lombok.Data;
import java.time.LocalDateTime;

@Data
public class SubCategoryVO {
    private Long id;
    private String name;
    private Long categoryId;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
