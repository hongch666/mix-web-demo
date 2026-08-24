package com.hcsy.spring.entity.vo;

import java.util.Map;

import com.hcsy.spring.entity.dto.CommentScoreDTO;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 文章评论评分视图对象，用于批量查询评论评分结果。
 * 使用具体元素类型承载，避免 Map<Long, Map<String, CommentScoreDTO>> 泛型擦除导致 Jackson 序列化失败。
 */
@Data
@AllArgsConstructor
@NoArgsConstructor
public class ArticleCommentScoresVO {
    private Long articleId;
    private Map<String, CommentScoreDTO> roleScores;
}
