package com.hcsy.spring.entity.vo;

import java.util.List;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 批量文章统计视图对象，一次返回阅读量、点赞、收藏、粉丝与评论评分
 */
@Data
@AllArgsConstructor
@NoArgsConstructor
@Schema(description = "批量文章统计数据")
public class ArticleStatsBatchVO {
    @Schema(description = "文章阅读量列表")
    private List<IdCountVO> views;

    @Schema(description = "文章点赞数列表")
    private List<IdCountVO> likes;

    @Schema(description = "文章收藏数列表")
    private List<IdCountVO> collects;

    @Schema(description = "作者粉丝数列表")
    private List<IdCountVO> follows;

    @Schema(description = "文章评论评分列表")
    private List<ArticleCommentScoresVO> commentScores;
}
