package com.hcsy.spring.api.service.impl;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Set;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.domain.PageRequest;
import org.springframework.transaction.reactive.TransactionalOperator;

import com.hcsy.spring.api.repository.FocusRepository;
import com.hcsy.spring.api.repository.UserRepository;
import com.hcsy.spring.common.constants.Defaults;
import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.exceptions.BusinessException;
import com.hcsy.spring.entity.po.Focus;
import com.hcsy.spring.entity.po.User;
import com.hcsy.spring.entity.projection.IdCountRow;
import com.hcsy.spring.entity.vo.FocusSyncVO;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

@ExtendWith(MockitoExtension.class)
class FocusServiceImplTest {

    private static final Long USER_ID = 3L;
    private static final Long TARGET_ID = 4L;
    private static final LocalDateTime CREATED_TIME = LocalDateTime.parse("2026-03-01T12:00:00");

    @Mock
    private FocusRepository focusRepository;
    @Mock
    private UserRepository userRepository;
    @Mock
    private TransactionalOperator transactionalOperator;

    private FocusServiceImpl focusService;

    @BeforeEach
    void setUp() {
        focusService = new FocusServiceImpl(focusRepository, userRepository, transactionalOperator);
    }

    @Test
    @DisplayName("重复关注返回失败且不写入记录")
    void addFocusRejectsDuplicate() {
        when(focusRepository.existsByUserIdAndFocusId(USER_ID, TARGET_ID)).thenReturn(Mono.just(true));
        stubTransactional();

        StepVerifier.create(focusService.addFocus(USER_ID, TARGET_ID))
            .expectNext(false)
            .verifyComplete();

        verify(focusRepository, never()).save(any(Focus.class));
    }

    @Test
    @DisplayName("首次关注写入记录并返回成功")
    void addFocusPersistsNewRecord() {
        when(focusRepository.existsByUserIdAndFocusId(USER_ID, TARGET_ID)).thenReturn(Mono.just(false));
        stubTransactional();
        when(focusRepository.save(any(Focus.class))).thenReturn(Mono.just(new Focus()));

        StepVerifier.create(focusService.addFocus(USER_ID, TARGET_ID))
            .expectNext(true)
            .verifyComplete();

        ArgumentCaptor<Focus> captor = ArgumentCaptor.forClass(Focus.class);
        verify(focusRepository).save(captor.capture());
        assertThat(captor.getValue().getUserId()).isEqualTo(USER_ID);
        assertThat(captor.getValue().getFocusId()).isEqualTo(TARGET_ID);
        assertThat(captor.getValue().getCreatedTime()).isNotNull();
    }

    @Test
    @DisplayName("取消未关注的记录返回失败且不执行删除")
    void removeFocusRejectsMissingRecord() {
        when(focusRepository.existsByUserIdAndFocusId(USER_ID, TARGET_ID)).thenReturn(Mono.just(false));
        stubTransactional();

        StepVerifier.create(focusService.removeFocus(USER_ID, TARGET_ID))
            .expectNext(false)
            .verifyComplete();

        verify(focusRepository, never()).deleteByUserIdAndFocusId(any(), any());
    }

    @Test
    @DisplayName("批量统计被关注数时空入参直接返回空结果")
    void getFollowCountsSkipsEmptyInput() {
        StepVerifier.create(focusService.getFollowCountsByUserIds(List.of()))
            .assertNext(counts -> assertThat(counts.getCounts()).isEmpty())
            .verifyComplete();

        verify(focusRepository, never()).countGroupByFocusIdIn(any());
    }

    @Test
    @DisplayName("批量统计被关注数时把投影转换为 ID 计数项")
    void getFollowCountsMapsRows() {
        IdCountRow row = mock(IdCountRow.class);
        when(row.getId()).thenReturn(TARGET_ID);
        when(row.getCount()).thenReturn(6L);
        when(focusRepository.countGroupByFocusIdIn(List.of(TARGET_ID))).thenReturn(Flux.just(row));

        StepVerifier.create(focusService.getFollowCountsByUserIds(List.of(TARGET_ID)))
            .assertNext(counts -> {
                assertThat(counts.getCounts()).hasSize(1);
                assertThat(counts.getCounts().get(0).getId()).isEqualTo(TARGET_ID);
                assertThat(counts.getCounts().get(0).getCount()).isEqualTo(6L);
            })
            .verifyComplete();
    }

    @Test
    @DisplayName("关注列表按被关注用户装配用户名与关注时间")
    void listUserFocusesMapsTargetUser() {
        when(focusRepository.findByUserIdOrderByCreatedTimeDesc(USER_ID, PageRequest.of(0, 10)))
            .thenReturn(Flux.just(focus()));
        when(focusRepository.countByUserId(USER_ID)).thenReturn(Mono.just(1L));
        when(userRepository.findAllById(Set.of(TARGET_ID)))
            .thenReturn(Flux.just(user(TARGET_ID, "bob")));

        StepVerifier.create(focusService.listUserFocuses(USER_ID, 1, 10))
            .assertNext(page -> {
                assertThat(page.getTotal()).isEqualTo(1L);
                assertThat(page.getRecords()).hasSize(1);
                assertThat(page.getRecords().get(0).getId()).isEqualTo(TARGET_ID);
                assertThat(page.getRecords().get(0).getName()).isEqualTo("bob");
                assertThat(page.getRecords().get(0).getFocusedTime()).isEqualTo(CREATED_TIME);
            })
            .verifyComplete();
    }

    @Test
    @DisplayName("关注列表存在已删除用户时返回未找到")
    void listUserFocusesRejectsMissingTargetUser() {
        when(focusRepository.findByUserIdOrderByCreatedTimeDesc(USER_ID, PageRequest.of(0, 10)))
            .thenReturn(Flux.just(focus()));
        when(focusRepository.countByUserId(USER_ID)).thenReturn(Mono.just(1L));
        when(userRepository.findAllById(Set.of(TARGET_ID))).thenReturn(Flux.empty());

        StepVerifier.create(focusService.listUserFocuses(USER_ID, 1, 10))
            .expectErrorMatches(error -> isBusinessError(error, HttpCode.NOT_FOUND, Messages.UNDEFINED_USER))
            .verify();
    }

    @Test
    @DisplayName("时间段内没有新增关注时返回零")
    void getFollowersInPeriodDefaultsToZero() {
        LocalDateTime start = LocalDateTime.parse("2026-03-01T00:00:00");
        LocalDateTime end = LocalDateTime.parse("2026-04-01T00:00:00");
        when(focusRepository.countFollowersInPeriod(USER_ID, start, end)).thenReturn(Mono.empty());

        StepVerifier.create(focusService.getFollowersInPeriod(USER_ID, start, end))
            .expectNext(0L)
            .verifyComplete();
    }

    @Test
    @DisplayName("全量同步关注时按上限抓取最近记录并转换关系视图")
    void getNeo4jSyncFocusUsesLimitedLatestQuery() {
        when(focusRepository.findLatestForSync(Defaults.NEO4J_SYNC_LIMIT)).thenReturn(Flux.just(focus()));

        StepVerifier.create(focusService.getNeo4jSyncFocus(null))
            .assertNext(list -> {
                assertThat(list).hasSize(1);
                FocusSyncVO vo = list.get(0);
                assertThat(vo.getUserId()).isEqualTo(USER_ID);
                assertThat(vo.getFocusId()).isEqualTo(TARGET_ID);
                assertThat(vo.getCreatedTime()).isEqualTo(CREATED_TIME);
            })
            .verifyComplete();
    }

    private void stubTransactional() {
        when(transactionalOperator.transactional(any(Mono.class)))
            .thenAnswer(invocation -> invocation.getArgument(0));
    }

    private Focus focus() {
        Focus focus = new Focus();
        focus.setUserId(USER_ID);
        focus.setFocusId(TARGET_ID);
        focus.setCreatedTime(CREATED_TIME);
        return focus;
    }

    private User user(Long id, String name) {
        User user = new User();
        user.setId(id);
        user.setName(name);
        user.setRole("user");
        return user;
    }

    private boolean isBusinessError(Throwable error, int expectedStatus, String expectedMessage) {
        return error instanceof BusinessException businessException
            && businessException.getHttpStatus() == expectedStatus
            && expectedMessage.equals(businessException.getErrorMessage());
    }
}
