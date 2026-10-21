package com.hcsy.spring.entity.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * AI 生成的评论响应，包含评论内容、星级评分、AI 类型与头像地址
 */
@Data
@AllArgsConstructor
@NoArgsConstructor
@Schema(description = "AI 评论")
public class AICommentsVO {
    @Schema(description = "评论内容")
    private String content;

    @Schema(description = "星级评分")
    private Double star;

    @Schema(description = "AI 类型")
    private String aiType;

    @Schema(description = "头像地址")
    private String pic;
}
