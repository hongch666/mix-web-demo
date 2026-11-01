package com.hcsy.spring.bootstrap;

import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.r2dbc.core.DatabaseClient;
import org.springframework.stereotype.Component;

import com.hcsy.spring.common.constants.Defaults;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.constants.Scripts;
import com.hcsy.spring.common.utils.SimpleLogger;

import io.r2dbc.spi.R2dbcException;
import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

/**
 * 数据库初始化器，应用就绪后按依赖顺序执行建表脚本并预置固定ID的AI用户数据
 */
@Component
@RequiredArgsConstructor
public class DatabaseInitializer {

    /** MySQL 重复索引名错误码，表示索引已存在，可安全跳过 */
    private static final String MYSQL_DUPLICATE_INDEX_ERROR = "1061";

    private final DatabaseClient databaseClient;
    private final SimpleLogger logger;

    /**
     * 应用就绪后触发数据库建表与AI用户预置数据的初始化
     */
    @EventListener(ApplicationReadyEvent.class)
    public void initialize() {
        initializeDatabase()
            .subscribe(
                ignored -> {
                },
                error -> logger.error(Messages.CREATE_TABLE, error),
                () -> logger.info(Messages.INIT_AI_SUCCESS));
    }

    /**
     * 编排建表与预置数据初始化，包私有以便单元测试直接订阅验证顺序与容错
     */
    Mono<Void> initializeDatabase() {
        Mono<Void> baseTables = Mono.when(
            execute(Scripts.CREATE_CATEGORY_TABLE),
            execute(Scripts.CREATE_USER_TABLE),
            execute(Scripts.CREATE_ARTICLES_TABLE),
            execute(Scripts.CREATE_COMMENTS_TABLE),
            execute(Scripts.CREATE_LIKES_TABLE),
            execute(Scripts.CREATE_COLLECTS_TABLE),
            execute(Scripts.CREATE_FOCUS_TABLE));

        return baseTables
            .then(execute(Scripts.CREATE_SUBCATEGORY_TABLE))
            .then(execute(Scripts.CREATE_CATEGORY_REFERENCE_TABLE))
            .then(ensureIndexes())
            .thenMany(Flux.concat(
                insertAIUserIfNotExists(Defaults.GLM_ID, Defaults.GLM_NAME,
                    Defaults.GLM_EMAIL, Defaults.GLM_IMG),
                insertAIUserIfNotExists(Defaults.GEMINI_ID, Defaults.GEMINI_NAME,
                    Defaults.GEMINI_EMAIL, Defaults.GEMINI_IMG),
                insertAIUserIfNotExists(Defaults.GPT_ID, Defaults.GPT_NAME,
                    Defaults.GPT_EMAIL, Defaults.GPT_IMG),
                insertAIUserIfNotExists(Defaults.DEEPSEEK_ID, Defaults.DEEPSEEK_NAME,
                    Defaults.DEEPSEEK_EMAIL, Defaults.DEEPSEEK_IMG),
                insertAIUserIfNotExists(Defaults.CLAUDE_ID, Defaults.CLAUDE_NAME,
                    Defaults.CLAUDE_EMAIL, Defaults.CLAUDE_IMG),
                insertAIUserIfNotExists(Defaults.QWEN_ID, Defaults.QWEN_NAME,
                    Defaults.QWEN_EMAIL, Defaults.QWEN_IMG)))
            .then();
    }

    /**
     * 逐条补齐建表语句未覆盖的索引
     *
     * ADD INDEX 在索引已存在时抛 1061，视为已存在跳过；其他失败只记日志不中断，
     * 避免个别索引问题拖垮整体初始化
     */
    private Mono<Void> ensureIndexes() {
        return Flux.fromIterable(Scripts.CREATE_INDEXES)
            .concatMap(index -> execute(createIndexSql(index))
                .doOnError(error -> logIndexError(index, error))
                .onErrorResume(error -> Mono.empty()))
            .then()
            .doOnSuccess(ignored -> logger.info(Messages.INDEX_INIT_SUCCESS));
    }

    /**
     * 拼装建索引语句，表名、索引名与列定义均来自常量，不接受外部输入
     */
    private String createIndexSql(Scripts.IndexDefinition index) {
        return "ALTER TABLE " + index.table() + " ADD INDEX " + index.name() + " " + index.columns();
    }

    /**
     * 区分“索引已存在”与其他建索引失败，分别降级为调试与错误日志
     */
    @SuppressWarnings("unlikely-arg-type")
    private void logIndexError(Scripts.IndexDefinition index, Throwable error) {
        if (error instanceof R2dbcException r2dbcError
            && MYSQL_DUPLICATE_INDEX_ERROR.equals(r2dbcError.getErrorCode())) {
            logger.debug(String.format(Messages.INDEX_EXIST, index.name()));
            return;
        }
        logger.error(String.format(Messages.INDEX_CREATE, index.name()), error);
    }

    /**
     * 执行单条建表或初始化 SQL
     */
    private Mono<Void> execute(String sql) {
        return databaseClient.sql(sql)
            .fetch()
            .rowsUpdated()
            .then();
    }

    /**
     * 按固定 ID 插入不存在的 AI 用户并记录插入结果
     */
    private Mono<Void> insertAIUserIfNotExists(Long id, String name, String email, String img) {
        return databaseClient.sql(Scripts.INSERT_AI_USER)
            .bind(0, id)
            .bind(1, name)
            .bind(2, Defaults.HIDE_PASSWORD)
            .bind(3, email)
            .bind(4, img)
            .fetch()
            .rowsUpdated()
            .doOnNext(updated -> {
                if (updated > 0) {
                    logger.info(String.format(Messages.AI_CREATED, name, id));
                } else {
                    logger.debug(String.format(Messages.AI_EXIST, id));
                }
            })
            .doOnError(error -> logger.error(String.format(Messages.AI_INSERT, id), error))
            .onErrorResume(error -> Mono.empty())
            .then();
    }
}
