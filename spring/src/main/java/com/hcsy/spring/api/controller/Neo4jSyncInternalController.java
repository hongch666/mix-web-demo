package com.hcsy.spring.api.controller;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.springframework.r2dbc.core.DatabaseClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.core.annotation.ApiLog;
import com.hcsy.spring.core.annotation.RequireInternalToken;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;

/**
 * Neo4j同步内部接口，统一由Spring读取MySQL业务表。
 */
@RestController
@RequestMapping("/neo4j-sync/internal")
@RequiredArgsConstructor
@Tag(name = "Neo4j同步内部接口", description = "供FastAPI同步Neo4j使用的业务数据接口")
public class Neo4jSyncInternalController {

    private final DatabaseClient databaseClient;

    @GetMapping("/snapshot")
    @Operation(summary = "获取Neo4j同步快照（内部）", description = "获取Spring管理的业务表快照，供FastAPI同步Neo4j")
    @RequireInternalToken
    @ApiLog("内部获取Neo4j同步快照")
    public Mono<Result<Map<String, List<Map<String, Object>>>>> getSnapshot(
        @RequestParam(required = false) String updatedAfter) {
        return Mono.zip(
            query("SELECT id, name, email, role, img, signature, created_at, updated_at FROM user", updatedAfter,
                "updated_at"),
            query("SELECT id, name, update_time FROM category", updatedAfter, "update_time"),
            query("SELECT id, name, category_id, update_time FROM sub_category", updatedAfter, "update_time"),
            query(
                "SELECT id, title, tags, status, views, user_id, sub_category_id, create_at, update_at, content FROM articles",
                updatedAfter, "update_at"),
            query("SELECT user_id, article_id, created_time FROM likes", updatedAfter, "created_time"),
            query("SELECT user_id, article_id, created_time FROM collects", updatedAfter, "created_time"),
            query("SELECT id, user_id, article_id, create_time, update_time FROM comments", updatedAfter,
                "update_time"),
            query("SELECT user_id, focus_id, created_time FROM focus", updatedAfter, "created_time")).map(tuple -> {
                Map<String, List<Map<String, Object>>> snapshot = new HashMap<>();
                snapshot.put("users", tuple.getT1());
                snapshot.put("categories", tuple.getT2());
                snapshot.put("sub_categories", tuple.getT3());
                snapshot.put("articles", tuple.getT4());
                snapshot.put("likes", tuple.getT5());
                snapshot.put("collects", tuple.getT6());
                snapshot.put("comments", tuple.getT7());
                snapshot.put("focus", tuple.getT8());
                return Result.success(snapshot);
            });
    }

    private Mono<List<Map<String, Object>>> query(
        String baseSql, String updatedAfter, String timestampColumn) {
        String sql = baseSql;
        DatabaseClient.GenericExecuteSpec spec;
        if (updatedAfter == null || updatedAfter.isBlank()) {
            spec = databaseClient.sql(sql);
        } else {
            sql += " WHERE " + timestampColumn + " > :updatedAfter";
            spec = databaseClient.sql(sql).bind("updatedAfter", updatedAfter);
        }
        return spec.map((row, metadata) -> {
            Map<String, Object> data = new HashMap<>();
            metadata.getColumnMetadatas().forEach(column -> data.put(column.getName(), row.get(column.getName())));
            return data;
        }).all().collectList();
    }
}
