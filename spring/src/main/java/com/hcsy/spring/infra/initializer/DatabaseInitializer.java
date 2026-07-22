package com.hcsy.spring.infra.initializer;

import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.r2dbc.core.DatabaseClient;
import org.springframework.stereotype.Component;

import com.hcsy.spring.common.constants.Defaults;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.constants.Scripts;
import com.hcsy.spring.common.utils.SimpleLogger;

import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

@Component
@RequiredArgsConstructor
public class DatabaseInitializer {

    private final DatabaseClient databaseClient;
    private final SimpleLogger logger;

    @EventListener(ApplicationReadyEvent.class)
    public void initialize() {
        initializeDatabase()
                .subscribe(
                        ignored -> { },
                        error -> logger.error(Messages.CREATE_TABLE, error),
                        () -> logger.info(Messages.INIT_AI_SUCCESS));
    }

    private Mono<Void> initializeDatabase() {
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
                .thenMany(Flux.concat(
                        insertAIUserIfNotExists(Defaults.DEEPSEEK_ID, Defaults.DEEPSEEK_NAME,
                                Defaults.DEEPSEEK_EMAIL, Defaults.DEEPSEEK_IMG),
                        insertAIUserIfNotExists(Defaults.GEMINI_ID, Defaults.GEMINI_NAME,
                                Defaults.GEMINI_EMAIL, Defaults.GEMINI_IMG),
                        insertAIUserIfNotExists(Defaults.GPT_ID, Defaults.GPT_NAME,
                                Defaults.GPT_EMAIL, Defaults.GPT_IMG)))
                .then();
    }

    @SuppressWarnings("null")
    private Mono<Void> execute(String sql) {
        return databaseClient.sql(sql)
                .fetch()
                .rowsUpdated()
                .then();
    }

    @SuppressWarnings("null")
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
