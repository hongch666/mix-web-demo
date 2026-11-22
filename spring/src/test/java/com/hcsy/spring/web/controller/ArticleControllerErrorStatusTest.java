package com.hcsy.spring.web.controller;

import static org.hamcrest.Matchers.equalTo;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import org.junit.jupiter.api.Test;
import org.springframework.test.web.reactive.server.WebTestClient;

import com.hcsy.spring.application.service.ArticleService;
import com.hcsy.spring.application.service.ArticleStatsService;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.entity.vo.ArticleWithCategoryVO;
import com.hcsy.spring.web.exception.GlobalExceptionHandler;

import reactor.core.publisher.Mono;

class ArticleControllerErrorStatusTest {
    private final ArticleService articleService = mock(ArticleService.class);
    private final WebTestClient client = WebTestClient
        .bindToController(new ArticleController(articleService, mock(ArticleStatsService.class)))
        .controllerAdvice(new GlobalExceptionHandler(mock(SimpleLogger.class)))
        .build();

    @Test
    void returnsNotFoundStatusWhenArticleDoesNotExist() {
        when(articleService.getArticleDetail(any())).thenReturn(Mono.empty());

        client.get().uri("/articles/{id}", 999).exchange()
            .expectStatus().isNotFound()
            .expectBody().jsonPath("$.code").value(equalTo(404));
    }

    @Test
    void returnsOkStatusWhenArticleExists() {
        when(articleService.getArticleDetail(any())).thenReturn(Mono.just(new ArticleWithCategoryVO()));

        client.get().uri("/articles/{id}", 1).exchange()
            .expectStatus().isOk()
            .expectBody().jsonPath("$.code").value(equalTo(200));
    }
}
