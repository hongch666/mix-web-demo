package com.hcsy.spring.entity.po;

import java.time.LocalDateTime;

import org.springframework.data.annotation.Id;
import org.springframework.data.relational.core.mapping.Table;

import lombok.Data;

@Data
@Table("likes")
public class ArticleLike {
    @Id
    private Long id;
    private Long articleId;
    private Long userId;
    private LocalDateTime createdTime;
}
