package com.hcsy.spring.entity.vo;

import java.time.LocalDateTime;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 用户与文章关系同步数据视图对象
 * 用于点赞、收藏等以「用户 - 文章」为两端的关系同步
 */
@Data
@AllArgsConstructor
@NoArgsConstructor
@Schema(description = "用户文章关系同步数据")
@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
public class ArticleRelationSyncVO {

    @Schema(description = "用户ID")
    private Long userId;

    @Schema(description = "文章ID")
    private Long articleId;

    @Schema(description = "关系创建时间")
    private LocalDateTime createdTime;
}
