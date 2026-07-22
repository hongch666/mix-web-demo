package com.hcsy.spring.api.service.impl;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.function.Function;
import java.util.stream.Collectors;

import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.reactive.TransactionalOperator;

import com.hcsy.spring.api.repository.FocusRepository;
import com.hcsy.spring.api.repository.UserRepository;
import com.hcsy.spring.api.service.FocusService;
import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.exceptions.BusinessException;
import com.hcsy.spring.core.annotation.ArticleSync;
import com.hcsy.spring.entity.dto.PageDTO;
import com.hcsy.spring.entity.po.Focus;
import com.hcsy.spring.entity.po.User;
import com.hcsy.spring.entity.vo.FocusUserVO;

import cn.hutool.core.bean.BeanUtil;
import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

@Service
@RequiredArgsConstructor
public class FocusServiceImpl implements FocusService {

    private final FocusRepository focusRepository;
    private final UserRepository userRepository;
    private final TransactionalOperator transactionalOperator;

    @SuppressWarnings("null")
    @Override
    @ArticleSync(action = "focus", description = Messages.ARTICLE_SYNC_FOCUS)
    public Mono<Boolean> addFocus(Long userId, Long focusId) {
        Mono<Boolean> operation = focusRepository.existsByUserIdAndFocusId(userId, focusId)
                .flatMap(exists -> {
                    if (exists) {
                        return Mono.just(false);
                    }
                    Focus focus = new Focus();
                    focus.setUserId(userId);
                    focus.setFocusId(focusId);
                    focus.setCreatedTime(LocalDateTime.now());
                    return focusRepository.save(focus).thenReturn(true);
                });
        return transactionalOperator.transactional(operation);
    }

    @SuppressWarnings("null")
    @Override
    @ArticleSync(action = "unfocus", description = Messages.ARTICLE_SYNC_UNFOCUS)
    public Mono<Boolean> removeFocus(Long userId, Long focusId) {
        return transactionalOperator.transactional(
                focusRepository.existsByUserIdAndFocusId(userId, focusId)
                        .flatMap(exists -> exists
                                ? focusRepository.deleteByUserIdAndFocusId(userId, focusId).thenReturn(true)
                                : Mono.just(false)));
    }

    @Override
    public Mono<Boolean> isFocused(Long userId, Long focusId) {
        return focusRepository.existsByUserIdAndFocusId(userId, focusId);
    }

    @SuppressWarnings("null")
    @Override
    public Mono<PageDTO<FocusUserVO>> listUserFocuses(Long userId, long page, long size) {
        Flux<Focus> query = focusRepository.findByUserIdOrderByCreatedTimeDesc(userId, pageRequest(page, size));
        return buildPage(query, focusRepository.countByUserId(userId), page, size, Focus::getFocusId);
    }

    @SuppressWarnings("null")
    @Override
    public Mono<PageDTO<FocusUserVO>> listUserFollowers(Long userId, long page, long size) {
        Flux<Focus> query = focusRepository.findByFocusIdOrderByCreatedTimeDesc(userId, pageRequest(page, size));
        return buildPage(query, focusRepository.countByFocusId(userId), page, size, Focus::getUserId);
    }

    @Override
    public Mono<Long> getFocusCountByUserId(Long userId) {
        return focusRepository.countByUserId(userId);
    }

    @Override
    public Mono<Long> getFollowerCountByUserId(Long userId) {
        return focusRepository.countByFocusId(userId);
    }

    @SuppressWarnings("null")
    private Mono<PageDTO<FocusUserVO>> buildPage(
            Flux<Focus> query,
            Mono<Long> total,
            long page,
            long size,
            Function<Focus, Long> relatedUserId) {
        Mono<List<FocusUserVO>> records = query.collectList().flatMap(focuses -> {
            Set<Long> userIds = focuses.stream().map(relatedUserId).collect(Collectors.toSet());
            return userRepository.findAllById(userIds)
                    .collectMap(User::getId, Function.identity())
                    .map(users -> toVOs(focuses, users, relatedUserId));
        });
        return Mono.zip(records, total).map(result -> {
            PageDTO<FocusUserVO> pageDTO = new PageDTO<>();
            pageDTO.setCurrent(page);
            pageDTO.setSize(size);
            pageDTO.setTotal(result.getT2());
            pageDTO.setRecords(result.getT1());
            return pageDTO;
        });
    }

    private List<FocusUserVO> toVOs(
            List<Focus> focuses,
            Map<Long, User> users,
            Function<Focus, Long> relatedUserId) {
        return focuses.stream().map(focus -> {
            User user = users.get(relatedUserId.apply(focus));
            if (user == null) {
                throw BusinessException.builder().httpStatus(HttpCode.NOT_FOUND)
                        .errorMessage(Messages.UNDEFINED_USER).build();
            }
            FocusUserVO vo = BeanUtil.copyProperties(user, FocusUserVO.class);
            vo.setFocusedTime(focus.getCreatedTime());
            return vo;
        }).toList();
    }

    private PageRequest pageRequest(long page, long size) {
        return PageRequest.of((int) Math.max(0, page - 1), (int) Math.max(1, Math.min(size, 1000)));
    }
}
