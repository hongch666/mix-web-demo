package com.hcsy.spring.api.service.impl;

import java.time.LocalDateTime;
import java.util.List;

import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.reactive.TransactionalOperator;

import com.hcsy.spring.api.repository.ArticleLikeRepository;
import com.hcsy.spring.api.service.ArticleLikeService;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.core.annotation.ArticleSync;
import com.hcsy.spring.entity.dto.PageDTO;
import com.hcsy.spring.entity.po.ArticleLike;
import com.hcsy.spring.entity.vo.ArticleLikeVO;

import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;

@Service
@RequiredArgsConstructor
public class ArticleLikeServiceImpl implements ArticleLikeService {

    private final ArticleLikeRepository articleLikeRepository;
    private final ArticleInteractionAssembler assembler;
    private final TransactionalOperator transactionalOperator;

    @SuppressWarnings("null")
    @Override
    @ArticleSync(action = "like", description = Messages.ARTICLE_SYNC_LIKE)
    public Mono<Boolean> addLike(Long articleId, Long userId) {
        Mono<Boolean> operation = articleLikeRepository.existsByArticleIdAndUserId(articleId, userId)
                .flatMap(exists -> {
                    if (exists) {
                        return Mono.just(false);
                    }
                    ArticleLike like = new ArticleLike();
                    like.setArticleId(articleId);
                    like.setUserId(userId);
                    like.setCreatedTime(LocalDateTime.now());
                    return articleLikeRepository.save(like).thenReturn(true);
                });
        return transactionalOperator.transactional(operation);
    }

    @SuppressWarnings("null")
    @Override
    @ArticleSync(action = "unlike", description = Messages.ARTICLE_SYNC_UNLIKE)
    public Mono<Boolean> removeLike(Long articleId, Long userId) {
        return transactionalOperator.transactional(
                articleLikeRepository.existsByArticleIdAndUserId(articleId, userId)
                        .flatMap(exists -> exists
                                ? articleLikeRepository.deleteByArticleIdAndUserId(articleId, userId).thenReturn(true)
                                : Mono.just(false)));
    }

    @Override
    public Mono<Boolean> isLiked(Long articleId, Long userId) {
        return articleLikeRepository.existsByArticleIdAndUserId(articleId, userId);
    }

    @Override
    public Mono<PageDTO<ArticleLikeVO>> listUserLikes(Long userId, long page, long size) {
        Mono<List<ArticleLikeVO>> records = articleLikeRepository
                .findByUserIdOrderByCreatedTimeDesc(userId, pageRequest(page, size))
                .collectList()
                .flatMap(assembler::toLikeVOs);
        return Mono.zip(records, articleLikeRepository.countByUserId(userId))
                .map(result -> page(page, size, result.getT2(), result.getT1()));
    }

    @Override
    public Mono<Long> getLikeCountByArticleId(Long articleId) {
        return articleLikeRepository.countByArticleId(articleId);
    }

    private PageRequest pageRequest(long page, long size) {
        return PageRequest.of((int) Math.max(0, page - 1), (int) Math.max(1, Math.min(size, 1000)));
    }

    private PageDTO<ArticleLikeVO> page(long current, long size, long total, List<ArticleLikeVO> records) {
        PageDTO<ArticleLikeVO> result = new PageDTO<>();
        result.setCurrent(current);
        result.setSize(size);
        result.setTotal(total);
        result.setRecords(records);
        return result;
    }
}
