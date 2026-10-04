package com.hcsy.spring.entity.vo;

import java.time.LocalDateTime;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 文章同步数据视图对象
 * 用于 Neo4j 同步与内部统计接口，字段名与数据库列名保持一致
 */
@Data
@AllArgsConstructor
@NoArgsConstructor
@Schema(description = "文章同步数据")
@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
public class ArticleSyncVO {

    @Schema(description = "文章ID")
    private Long id;

    @Schema(description = "文章标题")
    private String title;

    @Schema(description = "文章正文")
    private String content;

    @Schema(description = "作者用户ID")
    private Long userId;

    @Schema(description = "标签，多个标签以逗号分隔")
    private String tags;

    @Schema(description = "文章状态，0 草稿，1 已发布")
    private Integer status;

    @Schema(description = "浏览量")
    private Integer views;

    @Schema(description = "子分类ID")
    private Integer subCategoryId;

    @Schema(description = "创建时间")
    private LocalDateTime createAt;

    @Schema(description = "更新时间")
    private LocalDateTime updateAt;
}
