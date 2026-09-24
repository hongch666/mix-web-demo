package com.hcsy.spring.entity.po;

import java.time.LocalDateTime;

import org.springframework.data.annotation.Id;
import org.springframework.data.relational.core.mapping.Table;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

@Data
@Table("likes")
@Schema(description = "文章点赞")
public class ArticleLike {
    @Schema(description = "点赞ID")
    @Id
    private Long id;

    @Schema(description = "文章ID")
    private Long articleId;

    @Schema(description = "用户ID")
    private Long userId;

    @Schema(description = "点赞时间")
    private LocalDateTime createdTime;
}
