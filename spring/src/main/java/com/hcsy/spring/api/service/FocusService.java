package com.hcsy.spring.api.service;

import com.hcsy.spring.entity.dto.PageDTO;
import com.hcsy.spring.entity.vo.FocusUserVO;

import reactor.core.publisher.Mono;

public interface FocusService {
    Mono<Boolean> addFocus(Long userId, Long focusId);

    Mono<Boolean> removeFocus(Long userId, Long focusId);

    Mono<Boolean> isFocused(Long userId, Long focusId);

    Mono<PageDTO<FocusUserVO>> listUserFocuses(Long userId, long page, long size);

    Mono<PageDTO<FocusUserVO>> listUserFollowers(Long userId, long page, long size);

    Mono<Long> getFocusCountByUserId(Long userId);

    Mono<Long> getFollowerCountByUserId(Long userId);
}
