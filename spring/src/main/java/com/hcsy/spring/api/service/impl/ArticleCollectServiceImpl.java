package com.hcsy.spring.api.service.impl;

import java.time.LocalDateTime;
import java.util.List;

import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.reactive.TransactionalOperator;

import com.hcsy.spring.api.repository.ArticleCollectRepository;
import com.hcsy.spring.api.service.ArticleCollectService;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.core.annotation.ArticleSync;
import com.hcsy.spring.entity.dto.PageDTO;
import com.hcsy.spring.entity.po.ArticleCollect;
import com.hcsy.spring.entity.vo.ArticleCollectVO;

import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;

@Service
@RequiredArgsConstructor
public class ArticleCollectServiceImpl implements ArticleCollectService {

    private final ArticleCollectRepository articleCollectRepository;
    private final ArticleInteractionAssembler assembler;
    private final TransactionalOperator transactionalOperator;

    @SuppressWarnings("null")
    @Override
    @ArticleSync(action = "collect", description = Messages.ARTICLE_SYNC_COLLECT)
    public Mono<Boolean> addCollect(Long articleId, Long userId) {
        Mono<Boolean> operation = articleCollectRepository.existsByArticleIdAndUserId(articleId, userId)
                .flatMap(exists -> {
                    if (exists) {
                        return Mono.just(false);
                    }
                    ArticleCollect collect = new ArticleCollect();
                    collect.setArticleId(articleId);
                    collect.setUserId(userId);
                    collect.setCreatedTime(LocalDateTime.now());
                    return articleCollectRepository.save(collect).thenReturn(true);
                });
        return transactionalOperator.transactional(operation);
    }

    @SuppressWarnings("null")
    @Override
    @ArticleSync(action = "uncollect", description = Messages.ARTICLE_SYNC_UNCOLLECT)
    public Mono<Boolean> removeCollect(Long articleId, Long userId) {
        return transactionalOperator.transactional(
                articleCollectRepository.existsByArticleIdAndUserId(articleId, userId)
                        .flatMap(exists -> exists
                                ? articleCollectRepository.deleteByArticleIdAndUserId(articleId, userId)
                                        .thenReturn(true)
                                : Mono.just(false)));
    }

    @Override
    public Mono<Boolean> isCollected(Long articleId, Long userId) {
        return articleCollectRepository.existsByArticleIdAndUserId(articleId, userId);
    }

    @Override
    public Mono<PageDTO<ArticleCollectVO>> listUserCollects(Long userId, long page, long size) {
        Mono<List<ArticleCollectVO>> records = articleCollectRepository
                .findByUserIdOrderByCreatedTimeDesc(userId, pageRequest(page, size))
                .collectList()
                .flatMap(assembler::toCollectVOs);
        return Mono.zip(records, articleCollectRepository.countByUserId(userId))
                .map(result -> page(page, size, result.getT2(), result.getT1()));
    }

    @Override
    public Mono<Long> getCollectCountByArticleId(Long articleId) {
        return articleCollectRepository.countByArticleId(articleId);
    }

    private PageRequest pageRequest(long page, long size) {
        return PageRequest.of((int) Math.max(0, page - 1), (int) Math.max(1, Math.min(size, 1000)));
    }

    private PageDTO<ArticleCollectVO> page(long current, long size, long total, List<ArticleCollectVO> records) {
        PageDTO<ArticleCollectVO> result = new PageDTO<>();
        result.setCurrent(current);
        result.setSize(size);
        result.setTotal(total);
        result.setRecords(records);
        return result;
    }
}
