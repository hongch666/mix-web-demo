package com.hcsy.spring.api.service.impl;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Collection;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.springframework.data.domain.Sort;
import org.springframework.data.r2dbc.core.R2dbcEntityTemplate;
import org.springframework.data.relational.core.query.Criteria;
import org.springframework.data.relational.core.query.Query;
import org.springframework.stereotype.Service;
import org.springframework.transaction.reactive.TransactionalOperator;

import com.hcsy.spring.api.repository.ArticleRepository;
import com.hcsy.spring.api.repository.CommentsRepository;
import com.hcsy.spring.api.repository.UserRepository;
import com.hcsy.spring.api.service.CommentsService;
import com.hcsy.spring.common.constants.Defaults;
import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.exceptions.BusinessException;
import com.hcsy.spring.common.utils.Neo4jSyncMapUtil;
import com.hcsy.spring.entity.dto.CommentScoreDTO;
import com.hcsy.spring.entity.dto.CommentsQueryDTO;
import com.hcsy.spring.entity.dto.PageDTO;
import com.hcsy.spring.entity.po.Article;
import com.hcsy.spring.entity.po.Comments;
import com.hcsy.spring.entity.po.User;

import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

@Service
@RequiredArgsConstructor
public class CommentsServiceImpl implements CommentsService {

    private final CommentsRepository commentsRepository;
    private final ArticleRepository articleRepository;
    private final UserRepository userRepository;
    private final R2dbcEntityTemplate entityTemplate;
    private final TransactionalOperator transactionalOperator;

    @Override
    public Mono<PageDTO<Comments>> listCommentsWithFilter(long page, long size, CommentsQueryDTO queryDTO) {
        return listWithFilter(page, size, queryDTO, false);
    }

    @Override
    public Mono<PageDTO<Comments>> listAICommentsWithFilter(long page, long size, CommentsQueryDTO queryDTO) {
        return listWithFilter(page, size, queryDTO, true);
    }

    @Override
    public Mono<PageDTO<Comments>> listCommentsByUserId(long page, long size, Long userId) {
        Criteria criteria = Criteria.where("user_id").is(userId);
        return queryPage(criteria, page, size, Sort.by(Sort.Direction.DESC, "create_time"));
    }

    @Override
    public Mono<PageDTO<Comments>> listCommentsByArticleId(
        long page, long size, Long articleId, String sortWay) {
        return userRepository.findIdsByRoleNot(Defaults.AI_ROLE).collectList().flatMap(userIds -> {
            if (userIds.isEmpty()) {
                return Mono.just(emptyPage(page, size));
            }
            Criteria criteria = Criteria.where("article_id").is(articleId).and("user_id").in(userIds);
            Sort sort = "star".equals(sortWay)
                ? Sort.by(Sort.Direction.DESC, "star")
                : Sort.by(Sort.Direction.DESC, "create_time");
            return queryPage(criteria, page, size, sort);
        });
    }

    @Override
    public Flux<Comments> listAICommentsByArticleId(Long articleId) {
        return userRepository.findIdsByRole(Defaults.AI_ROLE).collectList().flatMapMany(userIds -> {
            if (userIds.isEmpty()) {
                return Flux.empty();
            }
            Query query = Query.query(Criteria.where("article_id").is(articleId).and("user_id").in(userIds))
                .sort(Sort.by(Sort.Direction.DESC, "create_time"));
            return entityTemplate.select(Comments.class).matching(query).all();
        });
    }

    @Override
    public Mono<Comments> save(Comments comments) {
        return transactionalOperator.transactional(commentsRepository.save(comments));
    }

    @Override
    public Mono<Comments> update(Comments comments) {
        return transactionalOperator.transactional(
            commentsRepository.findById(comments.getId())
                .switchIfEmpty(Mono.error(notFound(Messages.COMMENT_ID + comments.getId())))
                .flatMap(existing -> {
                    // 仅允许更新内容和评分，保留 userId/articleId/createTime 防止越权篡改
                    existing.setContent(comments.getContent());
                    existing.setStar(comments.getStar());
                    return commentsRepository.save(existing);
                }));
    }

    @Override
    public Mono<Comments> getById(Long id) {
        return commentsRepository.findById(id);
    }

    @Override
    public Mono<Void> deleteComment(Long id) {
        Mono<Void> operation = commentsRepository.findById(id)
            .switchIfEmpty(Mono.error(notFound(Messages.COMMENT_ID + id)))
            .flatMap(commentsRepository::delete);
        return transactionalOperator.transactional(operation);
    }

    @Override
    public Mono<Void> deleteComments(List<Long> ids) {
        List<Long> distinctIds = ids == null ? List.of()
            : ids.stream()
                .filter(id -> id != null).distinct().toList();
        if (distinctIds.isEmpty()) {
            return Mono.empty();
        }
        Mono<Void> operation = commentsRepository.findAllById(distinctIds)
            .count()
            .filter(count -> count == distinctIds.size())
            .switchIfEmpty(Mono.error(notFound(Messages.UNDEFINED_COMMENTS)))
            .then(commentsRepository.deleteAllById(distinctIds));
        return transactionalOperator.transactional(operation);
    }

    private Mono<PageDTO<Comments>> listWithFilter(
        long page, long size, CommentsQueryDTO queryDTO, boolean aiOnly) {
        Flux<Long> articleIds = hasText(queryDTO.getArticleTitle())
            ? articleRepository.findByTitleContaining(queryDTO.getArticleTitle()).map(Article::getId)
            : Flux.empty();
        Flux<Long> userIds;
        if (aiOnly) {
            userIds = hasText(queryDTO.getUsername())
                ? userRepository.findByNameContaining(queryDTO.getUsername())
                    .filter(user -> Defaults.AI_ROLE.equals(user.getRole())).map(User::getId)
                : userRepository.findIdsByRole(Defaults.AI_ROLE);
        } else {
            userIds = hasText(queryDTO.getUsername())
                ? userRepository.findByNameContaining(queryDTO.getUsername())
                    .filter(user -> !Defaults.AI_ROLE.equals(user.getRole())).map(User::getId)
                : userRepository.findIdsByRoleNot(Defaults.AI_ROLE);
        }

        Mono<List<Long>> articleIdList = articleIds.collectList();
        Mono<List<Long>> userIdList = userIds.collectList();
        return Mono.zip(articleIdList, userIdList).flatMap(filters -> {
            List<Long> articles = filters.getT1();
            List<Long> users = filters.getT2();
            if (users.isEmpty() || (hasText(queryDTO.getArticleTitle()) && articles.isEmpty())) {
                return Mono.just(emptyPage(page, size));
            }
            Criteria criteria = Criteria.where("user_id").in(users);
            if (hasText(queryDTO.getArticleTitle())) {
                criteria = criteria.and("article_id").in(articles);
            }
            if (hasText(queryDTO.getContent())) {
                criteria = criteria.and("content").like("%" + queryDTO.getContent() + "%");
            }
            return queryPage(criteria, page, size, Sort.by(Sort.Direction.DESC, "create_time"));
        });
    }

    private Mono<PageDTO<Comments>> queryPage(Criteria criteria, long page, long size, Sort sort) {
        long offset = Math.max(0, page - 1) * Math.max(1, size);
        int limit = (int) Math.max(1, Math.min(size, 1000));
        Query dataQuery = Query.query(criteria).sort(sort).offset(offset).limit(limit);
        Query countQuery = Query.query(criteria);
        Mono<List<Comments>> records = entityTemplate.select(Comments.class).matching(dataQuery).all().collectList();
        Mono<Long> total = entityTemplate.count(countQuery, Comments.class);
        return Mono.zip(records, total).map(result -> page(page, size, result.getT2(), result.getT1()));
    }

    private PageDTO<Comments> emptyPage(long current, long size) {
        return page(current, size, 0, List.of());
    }

    private PageDTO<Comments> page(long current, long size, long total, List<Comments> records) {
        PageDTO<Comments> result = new PageDTO<>();
        result.setCurrent(current);
        result.setSize(size);
        result.setTotal(total);
        result.setRecords(records);
        return result;
    }

    private boolean hasText(String value) {
        return value != null && !value.isBlank();
    }

    private BusinessException notFound(String message) {
        return BusinessException.builder().httpStatus(HttpCode.NOT_FOUND).errorMessage(message).build();
    }

    @Override
    public Mono<Map<Long, Map<String, CommentScoreDTO>>> getCommentScoresByArticleIds(Collection<Long> articleIds) {
        if (articleIds == null || articleIds.isEmpty()) {
            return Mono.just(Map.of());
        }
        // 批量查询评论评分，按角色（ai/user）分组，与 gozero COMMENT_RATING_QUERY 逻辑一致
        return Flux.fromIterable(articleIds)
            .flatMap(articleId -> {
                Criteria criteria = Criteria.where("article_id").is(articleId).and("star").greaterThan(0);
                Query query = Query.query(criteria);
                return entityTemplate.select(Comments.class).matching(query).all()
                    .collectList()
                    .flatMap(comments -> {
                        if (comments.isEmpty()) {
                            return Mono.just(Map.entry(articleId, Map.<String, CommentScoreDTO>of()));
                        }
                        List<Long> userIds = comments.stream().map(Comments::getUserId).distinct().toList();
                        return userRepository.findAllById(userIds)
                            .collectMap(User::getId, User::getRole)
                            .map(userRoleMap -> {
                                Map<String, CommentScoreDTO> roleScores = new HashMap<>();
                                // 按角色分组计算平均分和数量
                                double aiSum = 0;
                                long aiCount = 0;
                                double userSum = 0;
                                long userCount = 0;
                                for (Comments c : comments) {
                                    String role = userRoleMap.getOrDefault(c.getUserId(), "user");
                                    if ("ai".equals(role)) {
                                        aiSum += c.getStar() != null ? c.getStar() : 0;
                                        aiCount++;
                                    } else {
                                        userSum += c.getStar() != null ? c.getStar() : 0;
                                        userCount++;
                                    }
                                }
                                if (aiCount > 0) {
                                    roleScores.put("ai", new CommentScoreDTO(aiSum / aiCount, aiCount));
                                }
                                if (userCount > 0) {
                                    roleScores.put("user", new CommentScoreDTO(userSum / userCount, userCount));
                                }
                                return Map.entry(articleId, roleScores);
                            });
                    });
            })
            .collectMap(Map.Entry::getKey, Map.Entry::getValue);
    }

    // ==================== 统计方法 ====================

    @Override
    public Mono<Long> getAiCommentsNumByArticleId(Long articleId) {
        return commentsRepository.countAiCommentsByArticleId(articleId).defaultIfEmpty(0L);
    }

    @Override
    public Mono<Void> deleteAiCommentsByArticleId(Long articleId) {
        return commentsRepository.deleteAiCommentsByArticleId(articleId).then();
    }

    @Override
    public Mono<Map<String, Object>> getMonthlyCommentTrend(Long userId) {
        LocalDate today = LocalDate.now();
        LocalDateTime firstDay = today.withDayOfMonth(1).atStartOfDay();
        LocalDateTime lastDay;
        if (today.getMonthValue() == 12) {
            lastDay = LocalDate.of(today.getYear() + 1, 1, 1).atStartOfDay();
        } else {
            lastDay = LocalDate.of(today.getYear(), today.getMonthValue() + 1, 1).atStartOfDay();
        }

        return commentsRepository.countMonthlyByUserIdGroupByDate(userId, firstDay, lastDay)
            .map(row -> {
                Map<String, Object> trend = new HashMap<>();
                trend.put("date", row.getDate().toString());
                trend.put("count", row.getCount());
                return trend;
            })
            .collectList()
            .map(dailyTrends -> {
                Map<String, Object> result = new HashMap<>();
                result.put("daily_trends", dailyTrends);
                long total = dailyTrends.stream()
                    .mapToLong(t -> ((Number) t.get("count")).longValue())
                    .sum();
                result.put("total", total);
                return result;
            });
    }

    @Override
    public Mono<List<Map<String, Object>>> getNeo4jSyncComments(String updatedAfter) {
        if (updatedAfter == null || updatedAfter.isBlank()) {
            return commentsRepository.findAll()
                .map(Neo4jSyncMapUtil::commentToMap)
                .collectList()
                .map(list -> list.isEmpty() ? new ArrayList<>() : list);
        }
        LocalDateTime after = LocalDateTime.parse(updatedAfter);
        return commentsRepository.findByUpdateTimeAfter(after)
            .map(Neo4jSyncMapUtil::commentToMap)
            .collectList()
            .map(list -> list.isEmpty() ? new ArrayList<>() : list);
    }
}
