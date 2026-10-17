package com.hcsy.spring.bootstrap;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyInt;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.r2dbc.core.DatabaseClient;
import org.springframework.r2dbc.core.FetchSpec;

import com.hcsy.spring.common.constants.Defaults;
import com.hcsy.spring.common.constants.Scripts;
import com.hcsy.spring.common.utils.SimpleLogger;

import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

/**
 * DatabaseInitializer 单元测试
 * Mock DatabaseClient 验证建表编排顺序、AI 预置用户绑定参数与失败容错
 * 不连接真实数据库
 */
@ExtendWith(MockitoExtension.class)
class DatabaseInitializerTest {

    private static final String[] BASE_TABLE_SCRIPTS = {
        Scripts.CREATE_CATEGORY_TABLE,
        Scripts.CREATE_USER_TABLE,
        Scripts.CREATE_ARTICLES_TABLE,
        Scripts.CREATE_COMMENTS_TABLE,
        Scripts.CREATE_LIKES_TABLE,
        Scripts.CREATE_COLLECTS_TABLE,
        Scripts.CREATE_FOCUS_TABLE
    };

    private static final Long[] AI_USER_IDS = {
        Defaults.GLM_ID,
        Defaults.GEMINI_ID,
        Defaults.GPT_ID,
        Defaults.DEEPSEEK_ID,
        Defaults.CLAUDE_ID,
        Defaults.QWEN_ID
    };

    private static final String[] AI_USER_NAMES = {
        Defaults.GLM_NAME,
        Defaults.GEMINI_NAME,
        Defaults.GPT_NAME,
        Defaults.DEEPSEEK_NAME,
        Defaults.CLAUDE_NAME,
        Defaults.QWEN_NAME
    };

    private static final String[] AI_USER_EMAILS = {
        Defaults.GLM_EMAIL,
        Defaults.GEMINI_EMAIL,
        Defaults.GPT_EMAIL,
        Defaults.DEEPSEEK_EMAIL,
        Defaults.CLAUDE_EMAIL,
        Defaults.QWEN_EMAIL
    };

    private DatabaseClient databaseClient;
    private SimpleLogger logger;
    private DatabaseInitializer initializer;

    private final List<String> executedSql = new ArrayList<>();
    private final Map<String, Mono<Long>> sqlResults = new HashMap<>();
    private final Deque<Mono<Long>> insertResults = new ArrayDeque<>();
    private final List<List<Object[]>> insertBinds = new ArrayList<>();

    @BeforeEach
    void setUp() {
        databaseClient = mock(DatabaseClient.class);
        logger = mock(SimpleLogger.class);
        initializer = new DatabaseInitializer(databaseClient, logger);
        when(databaseClient.sql(anyString())).thenAnswer(invocation -> createSpec(invocation.getArgument(0)));
    }

    @Test
    @DisplayName("按基础表 → 子分类表 → 分类引用表 → AI 用户的顺序编排，共 15 条语句")
    void should_execute_statements_in_declared_order_and_total_15() {
        StepVerifier.create(initializer.initializeDatabase()).verifyComplete();

        assertThat(executedSql).hasSize(15);
        int subCategoryIndex = executedSql.indexOf(Scripts.CREATE_SUBCATEGORY_TABLE);
        assertThat(subCategoryIndex).isGreaterThan(-1);
        for (String script : BASE_TABLE_SCRIPTS) {
            assertThat(executedSql.indexOf(script)).isLessThan(subCategoryIndex);
        }
        assertThat(executedSql.indexOf(Scripts.CREATE_CATEGORY_REFERENCE_TABLE))
            .isGreaterThan(executedSql.indexOf(Scripts.CREATE_SUBCATEGORY_TABLE));
        assertThat(executedSql.indexOf(Scripts.INSERT_AI_USER))
            .isGreaterThan(executedSql.indexOf(Scripts.CREATE_CATEGORY_REFERENCE_TABLE));
        assertThat(executedSql).filteredOn(Scripts.INSERT_AI_USER::equals).hasSize(6);
    }

    @Test
    @DisplayName("AI 预置用户按声明顺序绑定 id、name、隐藏密码、email、img 五个参数")
    void should_bind_ai_user_fields_in_preset_order() {
        StepVerifier.create(initializer.initializeDatabase()).verifyComplete();

        assertThat(insertBinds).hasSize(6);
        for (int index = 0; index < insertBinds.size(); index++) {
            List<Object[]> binds = insertBinds.get(index);
            assertThat(binds).hasSize(5);
            assertThat(binds.get(0)).containsExactly(0, AI_USER_IDS[index]);
            assertThat(binds.get(1)).containsExactly(1, AI_USER_NAMES[index]);
            assertThat(binds.get(2)).containsExactly(2, Defaults.HIDE_PASSWORD);
            assertThat(binds.get(3)).containsExactly(3, AI_USER_EMAILS[index]);
            assertThat(binds.get(4)[0]).isEqualTo(4);
        }
    }

    @Test
    @DisplayName("单个 AI 用户插入失败时整体仍完成，其余用户照常插入")
    void should_complete_and_keep_inserting_when_single_ai_user_insert_fails() {
        insertResults.add(Mono.error(new RuntimeException("insert failed")));

        StepVerifier.create(initializer.initializeDatabase()).verifyComplete();

        assertThat(executedSql).filteredOn(Scripts.INSERT_AI_USER::equals).hasSize(6);
    }

    @Test
    @DisplayName("基础表创建失败时中断编排，后续语句与 AI 用户插入均不执行")
    void should_abort_remaining_statements_when_base_table_creation_fails() {
        sqlResults.put(Scripts.CREATE_ARTICLES_TABLE, Mono.error(new RuntimeException("create failed")));

        StepVerifier.create(initializer.initializeDatabase()).verifyError();

        assertThat(executedSql).doesNotContain(Scripts.CREATE_SUBCATEGORY_TABLE);
        assertThat(executedSql).doesNotContain(Scripts.CREATE_CATEGORY_REFERENCE_TABLE);
        assertThat(executedSql).doesNotContain(Scripts.INSERT_AI_USER);
    }

    private DatabaseClient.GenericExecuteSpec createSpec(String sql) {
        DatabaseClient.GenericExecuteSpec spec = mock(DatabaseClient.GenericExecuteSpec.class);
        @SuppressWarnings("unchecked")
        FetchSpec<Map<String, Object>> fetch = mock(FetchSpec.class);
        when(spec.fetch()).thenReturn(fetch);
        when(fetch.rowsUpdated()).thenAnswer(invocation -> Mono.defer(() -> {
            executedSql.add(sql);
            return resolveResult(sql);
        }));
        if (Scripts.INSERT_AI_USER.equals(sql)) {
            List<Object[]> binds = new ArrayList<>();
            insertBinds.add(binds);
            when(spec.bind(anyInt(), any())).thenAnswer(bindInvocation -> {
                binds.add(new Object[] { bindInvocation.getArgument(0), bindInvocation.getArgument(1) });
                return spec;
            });
        }
        return spec;
    }

    private Mono<Long> resolveResult(String sql) {
        if (Scripts.INSERT_AI_USER.equals(sql)) {
            Mono<Long> queued = insertResults.poll();
            return queued == null ? Mono.just(1L) : queued;
        }
        return sqlResults.getOrDefault(sql, Mono.just(1L));
    }
}
