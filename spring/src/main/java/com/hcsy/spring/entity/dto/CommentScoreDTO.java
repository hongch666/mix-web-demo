package com.hcsy.spring.entity.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 评论评分DTO，用于内部批量查询
 */
@Data
@AllArgsConstructor
@NoArgsConstructor
@Schema(description = "评论评分统计")
public class CommentScoreDTO {
    @Schema(description = "平均评分")
    private Double averageScore;

    @Schema(description = "评论数量")
    private Long count;
}
