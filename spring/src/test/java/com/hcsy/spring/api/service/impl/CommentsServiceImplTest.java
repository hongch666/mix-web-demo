package com.hcsy.spring.api.service.impl;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyIterable;
import static org.mockito.ArgumentMatchers.anyList;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.r2dbc.core.R2dbcEntityTemplate;
import org.springframework.data.r2dbc.core.ReactiveSelectOperation;
import org.springframework.data.relational.core.query.Query;
import org.springframework.transaction.reactive.TransactionalOperator;

import com.hcsy.spring.api.repository.ArticleRepository;
import com.hcsy.spring.api.repository.CommentsRepository;
import com.hcsy.spring.api.repository.UserRepository;
import com.hcsy.spring.common.constants.Defaults;
import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.exceptions.BusinessException;
import com.hcsy.spring.entity.dto.CommentScoreDTO;
import com.hcsy.spring.entity.dto.CommentsQueryDTO;
import com.hcsy.spring.entity.po.Comments;
import com.hcsy.spring.entity.po.User;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

@ExtendWith(MockitoExtension.class)
class CommentsServiceImplTest {

    private static final Long COMMENT_ID = 3L;
    private static final Long ARTICLE_ID = 8L;
    private static final Long AUTHOR_ID = 9L;
    private static final Long AI_USER_ID = 1001L;
    private static final Long NORMAL_USER_ID = 9L;

    @Mock
    private CommentsRepository commentsRepository;
    @Mock
    private ArticleRepository articleRepository;
    @Mock
    private UserRepository userRepository;
    @Mock
    private R2dbcEntityTemplate entityTemplate;
    @Mock
    private TransactionalOperator transactionalOperator;

    private CommentsServiceImpl commentsService;

    @BeforeEach
    void setUp() {
        commentsService = new CommentsServiceImpl(commentsRepository, articleRepository, userRepository,
            entityTemplate, transactionalOperator);
    }

    @Test
    @DisplayName("更新不存在的评论返回未找到且不落库")
    void updateRejectsMissingComment() {
        Comments incoming = new Comments();
        incoming.setId(COMMENT_ID);
        when(commentsRepository.findById(COMMENT_ID)).thenReturn(Mono.empty());
        stubTransactional();

        StepVerifier.create(commentsService.update(incoming))
            .expectErrorMatches(error -> isBusinessError(error, HttpCode.NOT_FOUND,
                Messages.COMMENT_ID + COMMENT_ID))
            .verify();

        verify(commentsRepository, never()).save(any(Comments.class));
    }

    @Test
    @DisplayName("更新评论只允许改内容与评分并保留归属与创建时间")
    void updateKeepsOwnershipFields() {
        LocalDateTime createTime = LocalDateTime.parse("2026-01-01T10:00:00");
        Comments existing = comment(NORMAL_USER_ID);
        existing.setCreateTime(createTime);

        Comments incoming = new Comments();
        incoming.setId(COMMENT_ID);
        incoming.setContent("更新后的内容");
        incoming.setStar(5D);
        incoming.setUserId(999L);
        incoming.setArticleId(999L);

        when(commentsRepository.findById(COMMENT_ID)).thenReturn(Mono.just(existing));
        stubTransactional();
        when(commentsRepository.save(any(Comments.class)))
            .thenAnswer(invocation -> Mono.just(invocation.getArgument(0)));

        StepVerifier.create(commentsService.update(incoming))
            .assertNext(saved -> {
                assertThat(saved.getContent()).isEqualTo("更新后的内容");
                assertThat(saved.getStar()).isEqualTo(5D);
                assertThat(saved.getUserId()).isEqualTo(NORMAL_USER_ID);
                assertThat(saved.getArticleId()).isEqualTo(ARTICLE_ID);
                assertThat(saved.getCreateTime()).isEqualTo(createTime);
            })
            .verifyComplete();
    }

    @Test
    @DisplayName("删除不存在的评论返回未找到")
    void deleteCommentRejectsMissingComment() {
        when(commentsRepository.findById(COMMENT_ID)).thenReturn(Mono.empty());
        stubTransactional();

        StepVerifier.create(commentsService.deleteComment(COMMENT_ID))
            .expectErrorMatches(error -> isBusinessError(error, HttpCode.NOT_FOUND,
                Messages.COMMENT_ID + COMMENT_ID))
            .verify();

        verify(commentsRepository, never()).delete(any(Comments.class));
    }

    @Test
    @DisplayName("批量删除时空入参直接完成且不开启事务")
    void deleteCommentsSkipsEmptyInput() {
        StepVerifier.create(commentsService.deleteComments(List.of())).verifyComplete();
        StepVerifier.create(commentsService.deleteComments(null)).verifyComplete();

        verify(transactionalOperator, never()).transactional(any(Mono.class));
        verify(commentsRepository, never()).deleteAllById(anyIterable());
    }

    @Test
    @DisplayName("批量删除时存在不存在的评论则整体拒绝")
    void deleteCommentsRejectsPartiallyMissingComments() {
        when(commentsRepository.findAllById(List.of(1L, 2L))).thenReturn(Flux.just(comment(NORMAL_USER_ID)));
        when(commentsRepository.deleteAllById(List.of(1L, 2L))).thenReturn(Mono.empty());
        stubTransactional();

        StepVerifier.create(commentsService.deleteComments(List.of(1L, 2L)))
            .expectErrorMatches(error -> isBusinessError(error, HttpCode.NOT_FOUND, Messages.UNDEFINED_COMMENTS))
            .verify();

        verify(commentsRepository).findAllById(List.of(1L, 2L));
    }

    @Test
    @DisplayName("按 ID 批量查询时空入参直接返回空流")
    void listByIdsSkipsEmptyInput() {
        StepVerifier.create(commentsService.listByIds(List.of())).verifyComplete();
        StepVerifier.create(commentsService.listByIds(null)).verifyComplete();

        verify(commentsRepository, never()).findAllById(anyIterable());
    }

    @Test
    @DisplayName("按文章查询评论时没有普通用户直接返回空分页")
    void listCommentsByArticleIdReturnsEmptyWithoutNormalUsers() {
        when(userRepository.findIdsByRoleNot(Defaults.AI_ROLE)).thenReturn(Flux.empty());

        StepVerifier.create(commentsService.listCommentsByArticleId(1, 10, ARTICLE_ID, "star"))
            .assertNext(page -> {
                assertThat(page.getRecords()).isEmpty();
                assertThat(page.getTotal()).isZero();
            })
            .verifyComplete();
    }

    @Test
    @DisplayName("AI 评论筛选在没有 AI 用户时直接返回空分页")
    void listAiCommentsWithFilterReturnsEmptyWithoutAiUsers() {
        when(userRepository.findIdsByRole(Defaults.AI_ROLE)).thenReturn(Flux.empty());

        StepVerifier.create(commentsService.listAICommentsWithFilter(1, 10, new CommentsQueryDTO()))
            .assertNext(page -> assertThat(page.getRecords()).isEmpty())
            .verifyComplete();
    }

    @Test
    @DisplayName("批量查询评论评分时空入参直接返回空列表")
    void getCommentScoresSkipsEmptyInput() {
        StepVerifier.create(commentsService.getCommentScoresByArticleIds(List.of()))
            .assertNext(scores -> assertThat(scores).isEmpty())
            .verifyComplete();

        verify(entityTemplate, never()).select(any(Class.class));
    }

    @Test
    @DisplayName("批量查询评论评分时按 AI 与普通用户角色分别求平均")
    void getCommentScoresAggregatesByRole() {
        Comments aiFirst = comment(AI_USER_ID);
        aiFirst.setStar(8D);
        Comments userFirst = comment(NORMAL_USER_ID);
        userFirst.setStar(4D);
        Comments userSecond = comment(NORMAL_USER_ID);
        userSecond.setStar(6D);

        ReactiveSelectOperation.ReactiveSelect<Comments> select = mock(ReactiveSelectOperation.ReactiveSelect.class);
        ReactiveSelectOperation.TerminatingSelect<Comments> terminating = mock(
            ReactiveSelectOperation.TerminatingSelect.class);
        when(entityTemplate.select(Comments.class)).thenReturn(select);
        when(select.matching(any(Query.class))).thenReturn(terminating);
        when(terminating.all()).thenReturn(Flux.just(aiFirst, userFirst, userSecond));
        when(userRepository.findAllById(anyList()))
            .thenReturn(Flux.just(user(AI_USER_ID, Defaults.AI_ROLE), user(NORMAL_USER_ID, "user")));

        StepVerifier.create(commentsService.getCommentScoresByArticleIds(List.of(ARTICLE_ID)))
            .assertNext(scores -> {
                assertThat(scores).hasSize(1);
                Map<String, CommentScoreDTO> roleScores = scores.get(0).getRoleScores();
                assertThat(roleScores.get("ai").getAverageScore()).isEqualTo(8.0);
                assertThat(roleScores.get("ai").getCount()).isEqualTo(1L);
                assertThat(roleScores.get("user").getAverageScore()).isEqualTo(5.0);
                assertThat(roleScores.get("user").getCount()).isEqualTo(2L);
            })
            .verifyComplete();
    }

    @Test
    @DisplayName("没有 AI 用户时 AI 评论数直接返回零")
    void getAiCommentsNumReturnsZeroWithoutAiUsers() {
        when(userRepository.findIdsByRole(Defaults.AI_ROLE)).thenReturn(Flux.empty());

        StepVerifier.create(commentsService.getAiCommentsNumByArticleId(ARTICLE_ID))
            .expectNext(0L)
            .verifyComplete();

        verify(commentsRepository, never()).countByArticleIdAndUserIdIn(any(), anyList());
    }

    @Test
    @DisplayName("没有 AI 用户时删除 AI 评论直接完成且不访问评论表")
    void deleteAiCommentsSkipsWithoutAiUsers() {
        when(userRepository.findIdsByRole(Defaults.AI_ROLE)).thenReturn(Flux.empty());

        StepVerifier.create(commentsService.deleteAiCommentsByArticleId(ARTICLE_ID)).verifyComplete();

        verify(commentsRepository, never()).deleteByArticleIdAndUserIdIn(any(), anyList());
    }

    private void stubTransactional() {
        when(transactionalOperator.transactional(any(Mono.class)))
            .thenAnswer(invocation -> invocation.getArgument(0));
    }

    private Comments comment(Long userId) {
        Comments comments = new Comments();
        comments.setId(COMMENT_ID);
        comments.setUserId(userId);
        comments.setArticleId(ARTICLE_ID);
        return comments;
    }

    private User user(Long id, String role) {
        User user = new User();
        user.setId(id);
        user.setRole(role);
        return user;
    }

    private boolean isBusinessError(Throwable error, int expectedStatus, String expectedMessage) {
        return error instanceof BusinessException businessException
            && businessException.getHttpStatus() == expectedStatus
            && expectedMessage.equals(businessException.getErrorMessage());
    }
}
