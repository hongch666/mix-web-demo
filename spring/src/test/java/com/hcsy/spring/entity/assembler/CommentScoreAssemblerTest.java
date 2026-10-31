package com.hcsy.spring.entity.assembler;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyList;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.util.List;
import java.util.Map;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import com.hcsy.spring.common.constants.Defaults;
import com.hcsy.spring.entity.dto.CommentScoreDTO;
import com.hcsy.spring.entity.po.Comments;
import com.hcsy.spring.entity.po.User;
import com.hcsy.spring.infra.repository.CommentsRepository;
import com.hcsy.spring.infra.repository.UserRepository;

import reactor.core.publisher.Flux;
import reactor.test.StepVerifier;

@ExtendWith(MockitoExtension.class)
class CommentScoreAssemblerTest {

    private static final Long ARTICLE_ID = 8L;
    private static final Long AI_USER_ID = 1001L;
    private static final Long NORMAL_USER_ID = 9L;

    @Mock
    private CommentsRepository commentsRepository;
    @Mock
    private UserRepository userRepository;

    private CommentScoreAssembler commentScoreAssembler;

    @BeforeEach
    void setUp() {
        commentScoreAssembler = new CommentScoreAssembler(commentsRepository, userRepository);
    }

    @Test
    @DisplayName("入参为空时不查库直接返回空列表")
    void toScoresReturnsEmptyWithoutQuery() {
        StepVerifier.create(commentScoreAssembler.toScoresByArticleIds(List.of()))
            .assertNext(scores -> assertThat(scores).isEmpty())
            .verifyComplete();

        verify(commentsRepository, never()).findScoredByArticleIdIn(any());
    }

    @Test
    @DisplayName("无评分评论时返回空列表且不查用户角色")
    void toScoresReturnsEmptyWithoutComments() {
        when(commentsRepository.findScoredByArticleIdIn(List.of(ARTICLE_ID))).thenReturn(Flux.empty());

        StepVerifier.create(commentScoreAssembler.toScoresByArticleIds(List.of(ARTICLE_ID)))
            .assertNext(scores -> assertThat(scores).isEmpty())
            .verifyComplete();

        verify(userRepository, never()).findAllById(anyList());
    }

    @Test
    @DisplayName("按 AI 与普通用户角色分别求平均分与评论数")
    void toScoresAveragesByRole() {
        Comments aiComment = comment(AI_USER_ID, 8D);
        Comments userFirst = comment(NORMAL_USER_ID, 4D);
        Comments userSecond = comment(NORMAL_USER_ID, 6D);
        when(commentsRepository.findScoredByArticleIdIn(List.of(ARTICLE_ID)))
            .thenReturn(Flux.just(aiComment, userFirst, userSecond));
        when(userRepository.findAllById(anyList()))
            .thenReturn(Flux.just(user(AI_USER_ID, Defaults.AI_ROLE), user(NORMAL_USER_ID, Defaults.USER_ROLE)));

        StepVerifier.create(commentScoreAssembler.toScoresByArticleIds(List.of(ARTICLE_ID)))
            .assertNext(scores -> {
                assertThat(scores).hasSize(1);
                Map<String, CommentScoreDTO> roleScores = scores.get(0).getRoleScores();
                assertThat(roleScores.get(Defaults.AI_ROLE).getAverageScore()).isEqualTo(8.0);
                assertThat(roleScores.get(Defaults.AI_ROLE).getCount()).isEqualTo(1L);
                assertThat(roleScores.get(Defaults.USER_ROLE).getAverageScore()).isEqualTo(5.0);
                assertThat(roleScores.get(Defaults.USER_ROLE).getCount()).isEqualTo(2L);
            })
            .verifyComplete();
    }

    private Comments comment(Long userId, Double star) {
        Comments comments = new Comments();
        comments.setArticleId(ARTICLE_ID);
        comments.setUserId(userId);
        comments.setStar(star);
        return comments;
    }

    private User user(Long id, String role) {
        User user = new User();
        user.setId(id);
        user.setRole(role);
        return user;
    }
}
