package com.hcsy.spring.api.service.impl;

import java.util.List;

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
import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.exceptions.BusinessException;
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

    private static final String AI_ROLE = "ai";

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

    @SuppressWarnings("null")
    @Override
    public Mono<PageDTO<Comments>> listCommentsByUserId(long page, long size, Long userId) {
        Criteria criteria = Criteria.where("user_id").is(userId);
        return queryPage(criteria, page, size, Sort.by(Sort.Direction.DESC, "create_time"));
    }

    @SuppressWarnings("null")
    @Override
    public Mono<PageDTO<Comments>> listCommentsByArticleId(
            long page, long size, Long articleId, String sortWay) {
        return userRepository.findIdsByRoleNot(AI_ROLE).collectList().flatMap(userIds -> {
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

    @SuppressWarnings("null")
    @Override
    public Flux<Comments> listAICommentsByArticleId(Long articleId) {
        return userRepository.findIdsByRole(AI_ROLE).collectList().flatMapMany(userIds -> {
            if (userIds.isEmpty()) {
                return Flux.empty();
            }
            Query query = Query.query(Criteria.where("article_id").is(articleId).and("user_id").in(userIds))
                    .sort(Sort.by(Sort.Direction.DESC, "create_time"));
            return entityTemplate.select(Comments.class).matching(query).all();
        });
    }

    @SuppressWarnings("null")
    @Override
    public Mono<Comments> save(Comments comments) {
        return transactionalOperator.transactional(commentsRepository.save(comments));
    }

    @SuppressWarnings("null")
    @Override
    public Mono<Comments> update(Comments comments) {
        return transactionalOperator.transactional(
                commentsRepository.findById(comments.getId())
                        .switchIfEmpty(Mono.error(notFound(Messages.COMMENT_ID + comments.getId())))
                        .flatMap(existing -> {
                            comments.setCreateTime(existing.getCreateTime());
                            return commentsRepository.save(comments);
                        }));
    }

    @SuppressWarnings("null")
    @Override
    public Mono<Comments> getById(Long id) {
        return commentsRepository.findById(id);
    }

    @SuppressWarnings("null")
    @Override
    public Mono<Void> deleteComment(Long id) {
        Mono<Void> operation = commentsRepository.findById(id)
                .switchIfEmpty(Mono.error(notFound(Messages.COMMENT_ID + id)))
                .flatMap(commentsRepository::delete);
        return transactionalOperator.transactional(operation);
    }

    @SuppressWarnings("null")
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

    @SuppressWarnings("null")
    private Mono<PageDTO<Comments>> listWithFilter(
            long page, long size, CommentsQueryDTO queryDTO, boolean aiOnly) {
        Flux<Long> articleIds = hasText(queryDTO.getArticleTitle())
                ? articleRepository.findByTitleContaining(queryDTO.getArticleTitle()).map(Article::getId)
                : Flux.empty();
        Flux<Long> userIds;
        if (aiOnly) {
            userIds = hasText(queryDTO.getUsername())
                    ? userRepository.findByNameContaining(queryDTO.getUsername())
                            .filter(user -> AI_ROLE.equals(user.getRole())).map(User::getId)
                    : userRepository.findIdsByRole(AI_ROLE);
        } else {
            userIds = hasText(queryDTO.getUsername())
                    ? userRepository.findByNameContaining(queryDTO.getUsername())
                            .filter(user -> !AI_ROLE.equals(user.getRole())).map(User::getId)
                    : userRepository.findIdsByRoleNot(AI_ROLE);
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
        @SuppressWarnings("null")
        Query dataQuery = Query.query(criteria).sort(sort).offset(offset).limit(limit);
        @SuppressWarnings("null")
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
}
