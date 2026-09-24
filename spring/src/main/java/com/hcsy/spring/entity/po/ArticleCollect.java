package com.hcsy.spring.entity.po;

import java.time.LocalDateTime;

import org.springframework.data.annotation.Id;
import org.springframework.data.relational.core.mapping.Table;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

@Data
@Table("collects")
@Schema(description = "文章收藏")
public class ArticleCollect {
    @Schema(description = "收藏ID")
    @Id
    private Long id;

    @Schema(description = "文章ID")
    private Long articleId;

    @Schema(description = "用户ID")
    private Long userId;

    @Schema(description = "收藏时间")
    private LocalDateTime createdTime;
}
