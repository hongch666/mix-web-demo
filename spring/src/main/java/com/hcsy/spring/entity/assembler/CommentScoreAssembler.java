package com.hcsy.spring.entity.assembler;

import java.util.ArrayList;
import java.util.Collection;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.springframework.stereotype.Component;

import com.hcsy.spring.common.constants.Defaults;
import com.hcsy.spring.entity.dto.CommentScoreDTO;
import com.hcsy.spring.entity.po.Comments;
import com.hcsy.spring.entity.po.User;
import com.hcsy.spring.entity.vo.ArticleCommentScoresVO;
import com.hcsy.spring.infra.repository.CommentsRepository;
import com.hcsy.spring.infra.repository.UserRepository;

import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;

/**
 * 将多篇文章的评论按 AI 与普通用户角色汇总为平均评分，供批量统计复用
 */
@Component
@RequiredArgsConstructor
public class CommentScoreAssembler {

    private final CommentsRepository commentsRepository;
    private final UserRepository userRepository;

    /**
     * 批量计算多篇文章按角色分组后的评论平均分，入参为空时返回空列表
     */
    public Mono<List<ArticleCommentScoresVO>> toScoresByArticleIds(Collection<Long> articleIds) {
        if (articleIds == null || articleIds.isEmpty()) {
            return Mono.just(List.of());
        }
        return commentsRepository.findScoredByArticleIdIn(articleIds)
            .collectList()
            .flatMap(this::groupByArticleAndRole);
    }

    /**
     * 按文章与角色累加星级并求平均，转为具名 VO 列表避免 Map 泛型擦除
     */
    private Mono<List<ArticleCommentScoresVO>> groupByArticleAndRole(List<Comments> comments) {
        if (comments.isEmpty()) {
            return Mono.just(List.of());
        }
        List<Long> userIds = comments.stream().map(Comments::getUserId).distinct().toList();
        return userRepository.findAllById(userIds)
            .collectMap(User::getId, User::getRole)
            .map(userRoleMap -> {
                Map<Long, Map<String, CommentScoreDTO>> grouped = new HashMap<>();
                // 按文章、角色分组累加评分与数量
                for (Comments comment : comments) {
                    long articleId = comment.getArticleId();
                    double star = comment.getStar() != null ? comment.getStar() : 0;
                    String role = Defaults.AI_ROLE.equals(userRoleMap.get(comment.getUserId()))
                        ? Defaults.AI_ROLE
                        : Defaults.USER_ROLE;
                    CommentScoreDTO score = grouped
                        .computeIfAbsent(articleId, key -> new HashMap<>())
                        .computeIfAbsent(role, key -> new CommentScoreDTO(0.0, 0L));
                    score.setAverageScore(score.getAverageScore() + star);
                    score.setCount(score.getCount() + 1);
                }
                // 计算各角色平均分
                grouped.values().forEach(roleScores -> roleScores.values().forEach(score -> {
                    if (score.getCount() > 0) {
                        score.setAverageScore(score.getAverageScore() / score.getCount());
                    }
                }));
                List<ArticleCommentScoresVO> scores = new ArrayList<>(grouped.size());
                grouped
                    .forEach((articleId, roleScores) -> scores.add(new ArticleCommentScoresVO(articleId, roleScores)));
                return scores;
            });
    }
}
