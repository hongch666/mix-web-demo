package com.hcsy.spring.entity.po;

import java.time.LocalDateTime;

import org.springframework.data.annotation.Id;
import org.springframework.data.relational.core.mapping.Table;

import lombok.Data;

@Data
@Table("comments")
public class Comments {
    @Id
    private Long id;
    private String content;
    private Double star; // 星级评分，1~10
    private Long articleId;
    private Long userId;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
