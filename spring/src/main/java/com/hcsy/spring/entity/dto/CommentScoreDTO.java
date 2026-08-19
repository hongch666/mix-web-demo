package com.hcsy.spring.entity.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 评论评分DTO，用于内部批量查询
 */
@Data
@AllArgsConstructor
@NoArgsConstructor
public class CommentScoreDTO {
    private Double averageScore;
    private Long count;
}
