package com.hcsy.spring.entity.po;

import java.time.LocalDateTime;

import org.springframework.data.annotation.Id;
import org.springframework.data.relational.core.mapping.Table;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

@Data
@Table("comments")
@Schema(description = "评论")
public class Comments {
    @Schema(description = "评论ID")
    @Id
    private Long id;

    @Schema(description = "评论内容")
    private String content;

    @Schema(description = "星级评分，1到10")
    private Double star;

    @Schema(description = "文章ID")
    private Long articleId;

    @Schema(description = "用户ID")
    private Long userId;

    @Schema(description = "创建时间")
    private LocalDateTime createTime;

    @Schema(description = "更新时间")
    private LocalDateTime updateTime;
}
