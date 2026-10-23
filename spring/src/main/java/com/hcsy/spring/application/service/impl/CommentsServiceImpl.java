package com.hcsy.spring.application.service.impl;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Collection;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.function.Function;
import java.util.stream.Collectors;

import org.springframework.data.domain.Sort;
import org.springframework.data.r2dbc.core.R2dbcEntityTemplate;
import org.springframework.data.relational.core.query.Criteria;
import org.springframework.data.relational.core.query.Query;
import org.springframework.stereotype.Service;
import org.springframework.transaction.reactive.TransactionalOperator;

import com.hcsy.spring.application.service.CommentsService;
import com.hcsy.spring.common.constants.Defaults;
import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.exceptions.BusinessException;
import com.hcsy.spring.entity.dto.CommentCreateDTO;
import com.hcsy.spring.entity.dto.CommentScoreDTO;
import com.hcsy.spring.entity.dto.CommentUpdateDTO;
import com.hcsy.spring.entity.dto.CommentsQueryDTO;
import com.hcsy.spring.entity.dto.PageDTO;
import com.hcsy.spring.entity.po.Article;
import com.hcsy.spring.entity.po.Comments;
import com.hcsy.spring.entity.po.User;
import com.hcsy.spring.entity.vo.AICommentsVO;
import com.hcsy.spring.entity.vo.ArticleCommentScoresVO;
import com.hcsy.spring.entity.vo.CommentSyncVO;
import com.hcsy.spring.entity.vo.CommentsVO;
import com.hcsy.spring.entity.vo.MapDataVO;
import com.hcsy.spring.entity.vo.PageVO;
import com.hcsy.spring.infra.repository.ArticleRepository;
import com.hcsy.spring.infra.repository.CommentsRepository;
import com.hcsy.spring.infra.repository.UserRepository;

import cn.hutool.core.bean.BeanUtil;
import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

/**
 * CommentsService 的实现，按文章标题与用户名解析关联关系后在事务中维护评论，并批量补充评论视图中的用户与文章信息
 */
@Service
@RequiredArgsConstructor
public class CommentsServiceImpl implements CommentsService {

    private final CommentsRepository commentsRepository;
    private final ArticleRepository articleRepository;
    private final UserRepository userRepository;
    private final R2dbcEntityTemplate entityTemplate;
    private final TransactionalOperator transactionalOperator;

    /**
     * 实现按文章标题与用户名解析关联ID后创建评论
     */
    @Override
    public Mono<Comments> createComment(CommentCreateDTO dto) {
        return Mono.zip(articleRepository.findFirstByTitle(dto.getArticleTitle()),
            userRepository.findByName(dto.getUsername()))
            .flatMap(relations -> {
                Comments comment = BeanUtil.toBean(dto, Comments.class);
                comment.setArticleId(relations.getT1().getId());
                comment.setUserId(relations.getT2().getId());
                return save(comment);
            });
    }

    /**
     * 实现按文章标题与用户名校验存在性后更新评论
     */
    @Override
    public Mono<Comments> updateComment(CommentUpdateDTO dto) {
        Comments comment = BeanUtil.toBean(dto, Comments.class);
        return Mono.zip(
            articleRepository.findFirstByTitle(dto.getArticleTitle()),
            userRepository.findByName(dto.getUsername()))
            .flatMap(ignored -> update(comment));
    }

    /**
     * 实现查询单条评论详情并补充用户与文章信息
     */
    @Override
    public Mono<CommentsVO> getCommentDetail(Long id) {
        return getById(id).flatMap(this::toCommentsVO);
    }

    /**
     * 实现批量补充评论分页中的用户与文章信息
     */
    @Override
    public Mono<PageVO<CommentsVO>> listCommentDetails(PageDTO<Comments> page) {
        Set<Long> userIds = page.getRecords().stream().map(Comments::getUserId).collect(Collectors.toSet());
        Set<Long> articleIds = page.getRecords().stream().map(Comments::getArticleId).collect(Collectors.toSet());
        Mono<Map<Long, User>> users = userRepository.findAllById(userIds).collectMap(User::getId, Function.identity());
        Mono<Map<Long, Article>> articles = articleRepository.findAllById(articleIds)
            .collectMap(Article::getId, Function.identity());
        return Mono.zip(users, articles).map(relations -> {
            List<CommentsVO> records = page.getRecords().stream()
                .map(comment -> mapComment(comment, relations.getT1().get(comment.getUserId()),
                    relations.getT2().get(comment.getArticleId())))
                .toList();
            return new PageVO<>(page.getTotal(), records);
        });
    }

    /**
     * 实现查询文章AI评论并补充AI用户名称与头像
     */
    @Override
    public Mono<List<AICommentsVO>> listAICommentDetailsByArticleId(Long articleId) {
        return listAICommentsByArticleId(articleId).collectList().flatMap(comments -> {
            Set<Long> userIds = comments.stream().map(Comments::getUserId).collect(Collectors.toSet());
            return userRepository.findAllById(userIds).collectMap(User::getId, Function.identity())
                .map(users -> comments.stream().map(comment -> {
                    AICommentsVO vo = BeanUtil.copyProperties(comment, AICommentsVO.class);
                    User user = users.get(comment.getUserId());
                    vo.setAiType(user == null ? Defaults.DEFAULT_AI : user.getName());
                    vo.setPic(user == null ? null : user.getImg());
                    return vo;
                }).toList());
        });
    }

    /**
     * 实现按ID批量查询评论并转为Neo4j同步视图对象
     */
    @Override
    public Mono<List<CommentSyncVO>> getCommentSyncByIds(Collection<Long> ids) {
        return listByIds(ids)
            .map(comment -> new CommentSyncVO(comment.getId(), comment.getUserId(), comment.getArticleId(),
                comment.getStar(), comment.getCreateTime(), comment.getUpdateTime()))
            .collectList();
    }

    /**
     * 查询评论关联的用户与文章并组装为评论视图
     */
    private Mono<CommentsVO> toCommentsVO(Comments comment) {
        Mono<User> user = userRepository.findById(comment.getUserId()).defaultIfEmpty(new User());
        Mono<Article> article = articleRepository.findById(comment.getArticleId()).defaultIfEmpty(new Article());
        return Mono.zip(user, article).map(relations -> mapComment(comment, relations.getT1(), relations.getT2()));
    }

    /**
     * 将评论实体与用户、文章组装为视图对象，缺失时用默认值
     */
    private CommentsVO mapComment(Comments comment, User user, Article article) {
        CommentsVO vo = BeanUtil.copyProperties(comment, CommentsVO.class);
        vo.setUsername(user == null || user.getName() == null ? Defaults.DEFAULT_USER : user.getName());
        vo.setPic(user == null ? null : user.getImg());
        vo.setArticleTitle(
            article == null || article.getTitle() == null ? Defaults.DEFAULT_ARTICLE : article.getTitle());
        return vo;
    }

    /**
     * 实现按用户名、文章标题、内容条件分页查询普通用户评论
     */
    @Override
    public Mono<PageDTO<Comments>> listCommentsWithFilter(long page, long size, CommentsQueryDTO queryDTO) {
        return listWithFilter(page, size, queryDTO, false);
    }

    /**
     * 实现按条件分页查询AI用户评论
     */
    @Override
    public Mono<PageDTO<Comments>> listAICommentsWithFilter(long page, long size, CommentsQueryDTO queryDTO) {
        return listWithFilter(page, size, queryDTO, true);
    }

    /**
     * 实现分页查询指定用户的评论，按创建时间倒序
     */
    @Override
    public Mono<PageDTO<Comments>> listCommentsByUserId(long page, long size, Long userId) {
        Criteria criteria = Criteria.where("user_id").is(userId);
        return queryPage(criteria, page, size, Sort.by(Sort.Direction.DESC, "create_time"));
    }

    /**
     * 实现分页查询文章下普通用户评论，支持按评分或时间排序
     */
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

    /**
     * 实现流式查询文章下所有AI用户评论
     */
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

    /**
     * 实现在事务中保存评论实体
     */
    @Override
    public Mono<Comments> save(Comments comments) {
        return transactionalOperator.transactional(commentsRepository.save(comments));
    }

    /**
     * 实现在事务中更新评论，仅允许修改内容与评分防止越权
     */
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

    /**
     * 实现按ID批量流式查询评论，空入参返回空流
     */
    @Override
    public Flux<Comments> listByIds(Collection<Long> ids) {
        if (ids == null || ids.isEmpty()) {
            return Flux.empty();
        }
        return commentsRepository.findAllById(ids);
    }

    /**
     * 实现按ID查询单条评论
     */
    @Override
    public Mono<Comments> getById(Long id) {
        return commentsRepository.findById(id);
    }

    /**
     * 实现删除指定评论，评论不存在时抛404异常
     */
    @Override
    public Mono<Void> deleteComment(Long id) {
        Mono<Void> operation = commentsRepository.findById(id)
            .switchIfEmpty(Mono.error(notFound(Messages.COMMENT_ID + id)))
            .flatMap(commentsRepository::delete);
        return transactionalOperator.transactional(operation);
    }

    /**
     * 实现批量删除评论，任一ID不存在时抛404异常
     */
    @Override
    public Mono<Void> deleteComments(List<Long> ids) {
        List<Long> distinctIds = ids == null
            ? List.of()
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

    /**
     * 按角色过滤用户并结合文章标题与内容条件动态拼装评论分页查询
     */
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

    /**
     * 按条件与排序执行评论分页查询，同时返回记录与总数
     */
    private Mono<PageDTO<Comments>> queryPage(Criteria criteria, long page, long size, Sort sort) {
        long offset = Math.max(0, page - 1) * Math.max(1, size);
        int limit = (int) Math.max(1, Math.min(size, 1000));
        Query dataQuery = Query.query(criteria).sort(sort).offset(offset).limit(limit);
        Query countQuery = Query.query(criteria);
        Mono<List<Comments>> records = entityTemplate.select(Comments.class).matching(dataQuery).all().collectList();
        Mono<Long> total = entityTemplate.count(countQuery, Comments.class);
        return Mono.zip(records, total).map(result -> page(page, size, result.getT2(), result.getT1()));
    }

    /**
     * 构造总数为0的空评论分页结果
     */
    private PageDTO<Comments> emptyPage(long current, long size) {
        return page(current, size, 0, List.of());
    }

    /**
     * 组装评论分页结果的当前页、页大小、总数与记录
     */
    private PageDTO<Comments> page(long current, long size, long total, List<Comments> records) {
        PageDTO<Comments> result = new PageDTO<>();
        result.setCurrent(current);
        result.setSize(size);
        result.setTotal(total);
        result.setRecords(records);
        return result;
    }

    /**
     * 判断字符串非null且非空白
     */
    private boolean hasText(String value) {
        return value != null && !value.isBlank();
    }

    /**
     * 构造404资源不存在的业务异常
     */
    private BusinessException notFound(String message) {
        return BusinessException.builder().httpStatus(HttpCode.NOT_FOUND).errorMessage(message).build();
    }

    /**
     * 实现批量查询文章评论评分并按AI与普通用户角色分组计算平均分
     */
    @Override
    public Mono<List<ArticleCommentScoresVO>> getCommentScoresByArticleIds(Collection<Long> articleIds) {
        if (articleIds == null || articleIds.isEmpty()) {
            return Mono.just(List.of());
        }
        // 批量查询评论评分，按角色（ai/user）分组，与 gozero COMMENT_RATING_QUERY 逻辑一致，优化：一次 in 查询拉取所有文章的相关评论，避免逐篇文章发起查询导致的 N+1 性能问题
        Criteria criteria = Criteria.where("article_id").in(articleIds).and("star").greaterThan(0);
        Query query = Query.query(criteria);
        return entityTemplate.select(Comments.class).matching(query).all()
            .collectList()
            .flatMap(comments -> {
                if (comments.isEmpty()) {
                    return Mono.just(List.of());
                }
                List<Long> userIds = comments.stream().map(Comments::getUserId).distinct().toList();
                return userRepository.findAllById(userIds)
                    .collectMap(User::getId, User::getRole)
                    .map(userRoleMap -> {
                        Map<Long, Map<String, CommentScoreDTO>> result = new HashMap<>();
                        // 按文章、角色分组累加评分与数量
                        for (Comments c : comments) {
                            long aid = c.getArticleId();
                            double star = c.getStar() != null ? c.getStar() : 0;
                            String role = "ai".equals(userRoleMap.getOrDefault(c.getUserId(), "user")) ? "ai" : "user";
                            Map<String, CommentScoreDTO> roleScores = result.computeIfAbsent(aid, k -> new HashMap<>());
                            CommentScoreDTO dto = roleScores.get(role);
                            if (dto == null) {
                                dto = new CommentScoreDTO(0.0, 0L);
                                roleScores.put(role, dto);
                            }
                            dto.setAverageScore(dto.getAverageScore() + star);
                            dto.setCount(dto.getCount() + 1);
                        }
                        // 计算各角色平均分
                        for (Map<String, CommentScoreDTO> roleScores : result.values()) {
                            for (CommentScoreDTO d : roleScores.values()) {
                                if (d.getCount() > 0) {
                                    d.setAverageScore(d.getAverageScore() / d.getCount());
                                }
                            }
                        }
                        // 转为具名 VO 列表，避免 Map<Long, Map<...>> 泛型擦除导致 Jackson 序列化失败
                        List<ArticleCommentScoresVO> voList = new ArrayList<>(result.size());
                        result
                            .forEach((articleId, scores) -> voList.add(new ArticleCommentScoresVO(articleId, scores)));
                        return voList;
                    });
            });
    }

    // ==================== 统计方法 ====================

    @Override
    public Mono<Long> getAiCommentsNumByArticleId(Long articleId) {
        return userRepository.findIdsByRole(Defaults.AI_ROLE)
            .collectList()
            .flatMap(aiUserIds -> {
                if (aiUserIds.isEmpty()) {
                    return Mono.just(0L);
                }
                return commentsRepository.countByArticleIdAndUserIdIn(articleId, aiUserIds).defaultIfEmpty(0L);
            });
    }

    /**
     * 实现删除文章下所有AI用户的评论
     */
    @Override
    public Mono<Void> deleteAiCommentsByArticleId(Long articleId) {
        return userRepository.findIdsByRole(Defaults.AI_ROLE)
            .collectList()
            .flatMap(aiUserIds -> {
                if (aiUserIds.isEmpty()) {
                    return Mono.empty();
                }
                return commentsRepository.deleteByArticleIdAndUserIdIn(articleId, aiUserIds).then();
            });
    }

    /**
     * 实现统计用户本月每日评论趋势与总数
     */
    @Override
    public Mono<MapDataVO> getMonthlyCommentTrend(Long userId) {
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
                return new MapDataVO(result);
            });
    }

    /**
     * 实现查询评论数据用于Neo4j同步，全量时仅取最近限定条数
     */
    @Override
    public Mono<List<CommentSyncVO>> getNeo4jSyncComments(String updatedAfter) {
        // 评论表数据量较大，全量同步仅取最近 NEO4J_SYNC_LIMIT 条，避免一次性加载全部导致耗时过长、连接/令牌超时
        if (updatedAfter == null || updatedAfter.isBlank()) {
            return commentsRepository.findLatestForSync(Defaults.NEO4J_SYNC_LIMIT)
                .map(this::commentToVO)
                .collectList()
                .map(list -> list.isEmpty() ? new ArrayList<>() : list);
        }
        LocalDateTime after = LocalDateTime.parse(updatedAfter);
        return commentsRepository.findLatestAfterForSync(after, Defaults.NEO4J_SYNC_LIMIT)
            .map(this::commentToVO)
            .collectList()
            .map(list -> list.isEmpty() ? new ArrayList<>() : list);
    }

    /**
     * 评论实体转同步视图对象，字段名与数据库列名保持一致，用于 Neo4j 同步
     */
    private CommentSyncVO commentToVO(Comments comment) {
        return new CommentSyncVO(
            comment.getId(),
            comment.getUserId(),
            comment.getArticleId(),
            comment.getStar(),
            comment.getCreateTime(),
            comment.getUpdateTime());
    }
}
