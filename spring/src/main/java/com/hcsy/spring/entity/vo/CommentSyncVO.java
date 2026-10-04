package com.hcsy.spring.entity.vo;

import java.time.LocalDateTime;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 评论同步数据视图对象
 * 用于 Neo4j 精确同步与内部批量查询接口
 */
@Data
@AllArgsConstructor
@NoArgsConstructor
@Schema(description = "评论同步数据")
@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
public class CommentSyncVO {

    @Schema(description = "评论ID")
    private Long id;

    @Schema(description = "评论作者用户ID")
    private Long userId;

    @Schema(description = "所属文章ID")
    private Long articleId;

    @Schema(description = "评论评分，未评分时为空")
    private Double star;

    @Schema(description = "创建时间")
    private LocalDateTime createTime;

    @Schema(description = "更新时间")
    private LocalDateTime updateTime;
}
