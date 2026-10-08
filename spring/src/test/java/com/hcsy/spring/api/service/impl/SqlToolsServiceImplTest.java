package com.hcsy.spring.api.service.impl;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Mockito.when;

import java.util.Map;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.r2dbc.core.DatabaseClient;
import org.springframework.r2dbc.core.FetchSpec;

import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.exceptions.BusinessException;
import com.hcsy.spring.common.utils.SimpleLogger;

import reactor.core.publisher.Flux;
import reactor.test.StepVerifier;

@ExtendWith(MockitoExtension.class)
class SqlToolsServiceImplTest {

    @Mock
    private DatabaseClient databaseClient;
    @Mock
    private DatabaseClient.GenericExecuteSpec executeSpec;
    @Mock
    private FetchSpec<Map<String, Object>> fetchSpec;
    @Mock
    private SimpleLogger logger;

    private SqlToolsServiceImpl sqlToolsService;

    @BeforeEach
    void setUp() {
        sqlToolsService = new SqlToolsServiceImpl(databaseClient, logger);
    }

    @Test
    @DisplayName("空查询语句被拒绝")
    void rejectsBlankQuery() {
        StepVerifier.create(sqlToolsService.executeQuery("   ", null))
            .expectErrorMatches(error -> error instanceof BusinessException businessException
                && Messages.SQL_PROXY_FORBIDDEN_STATEMENT.equals(businessException.getErrorMessage()))
            .verify();
    }

    @Test
    @DisplayName("多条语句被拒绝")
    void rejectsMultipleStatements() {
        StepVerifier.create(sqlToolsService.executeQuery("SELECT id FROM articles LIMIT 1; DROP TABLE user", null))
            .expectErrorMatches(error -> isBusinessError(error, HttpCode.BAD_REQUEST,
                Messages.SQL_PROXY_MULTIPLE_STATEMENTS))
            .verify();
    }

    @Test
    @DisplayName("非只读前缀的语句被拒绝")
    void rejectsNonReadonlyStatement() {
        StepVerifier.create(sqlToolsService.executeQuery("DELETE FROM articles LIMIT 1", null))
            .expectErrorMatches(error -> isBusinessError(error, HttpCode.BAD_REQUEST,
                Messages.SQL_PROXY_FORBIDDEN_STATEMENT))
            .verify();
    }

    @Test
    @DisplayName("查询非白名单表被拒绝")
    void rejectsTableOutsideWhitelist() {
        String expectedMessage = String.format(Messages.SQL_PROXY_TABLE_NOT_IN_WHITELIST, "secret_table");

        StepVerifier.create(sqlToolsService.executeQuery("SELECT id FROM secret_table LIMIT 5", null))
            .expectErrorMatches(error -> isBusinessError(error, HttpCode.BAD_REQUEST, expectedMessage))
            .verify();
    }

    @Test
    @DisplayName("缺少 LIMIT 的查询被拒绝")
    void rejectsQueryWithoutLimit() {
        StepVerifier.create(sqlToolsService.executeQuery("SELECT id FROM articles", null))
            .expectErrorMatches(error -> isBusinessError(error, HttpCode.BAD_REQUEST,
                Messages.SQL_PROXY_LIMIT_REQUIRED))
            .verify();
    }

    @Test
    @DisplayName("LIMIT 超过上限的查询被拒绝")
    void rejectsQueryBeyondMaxLimit() {
        StepVerifier.create(sqlToolsService.executeQuery("SELECT id FROM articles LIMIT 101", null))
            .expectErrorMatches(error -> isBusinessError(error, HttpCode.BAD_REQUEST,
                Messages.SQL_PROXY_LIMIT_EXCEEDED))
            .verify();
    }

    @Test
    @DisplayName("通过校验的查询按列顺序返回行数据")
    void executesValidQueryAndMapsRows() {
        String sql = "SELECT id FROM articles WHERE user_id = :uid LIMIT 10";
        when(databaseClient.sql(sql)).thenReturn(executeSpec);
        when(executeSpec.bind("uid", 7)).thenReturn(executeSpec);
        when(executeSpec.fetch()).thenReturn(fetchSpec);
        when(fetchSpec.all()).thenReturn(Flux.just(Map.of("id", 7L)));

        StepVerifier.create(sqlToolsService.executeQuery(sql, Map.of("uid", 7)))
            .assertNext(result -> {
                assertThat(result.getColumns()).containsExactly("id");
                assertThat(result.getRows()).hasSize(1);
                assertThat(result.getRows().get(0)).containsExactly(7L);
                assertThat(result.getRowCount()).isEqualTo(1);
            })
            .verifyComplete();
    }

    @Test
    @DisplayName("查询无结果时返回空结果集")
    void executesValidQueryWithoutRows() {
        String sql = "SELECT id FROM articles LIMIT 10";
        when(databaseClient.sql(sql)).thenReturn(executeSpec);
        when(executeSpec.fetch()).thenReturn(fetchSpec);
        when(fetchSpec.all()).thenReturn(Flux.empty());

        StepVerifier.create(sqlToolsService.executeQuery(sql, null))
            .assertNext(result -> {
                assertThat(result.getColumns()).isEmpty();
                assertThat(result.getRows()).isEmpty();
                assertThat(result.getRowCount()).isZero();
            })
            .verifyComplete();
    }

    @Test
    @DisplayName("仅带尾部单分号的查询被视为单条语句执行")
    void acceptsTrailingSemicolon() {
        when(databaseClient.sql("SELECT id FROM articles LIMIT 10")).thenReturn(executeSpec);
        when(executeSpec.fetch()).thenReturn(fetchSpec);
        when(fetchSpec.all()).thenReturn(Flux.just(Map.of("id", 1L)));

        StepVerifier.create(sqlToolsService.executeQuery("SELECT id FROM articles LIMIT 10; ", null))
            .assertNext(result -> assertThat(result.getRowCount()).isEqualTo(1))
            .verifyComplete();
    }

    @Test
    @DisplayName("查询表结构时非白名单表被拒绝")
    void rejectsTableSchemaOutsideWhitelist() {
        assertThatThrownBy(() -> sqlToolsService.getTables("secret_table"))
            .isInstanceOf(BusinessException.class)
            .hasMessage(String.format(Messages.SQL_PROXY_TABLE_NOT_IN_WHITELIST, "secret_table"));
    }

    private boolean isBusinessError(Throwable error, int expectedStatus, String expectedMessage) {
        return error instanceof BusinessException businessException
            && businessException.getHttpStatus() == expectedStatus
            && expectedMessage.equals(businessException.getErrorMessage());
    }
}
