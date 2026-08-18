package com.hcsy.spring.core.aspect;

import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.springframework.stereotype.Component;

import com.hcsy.spring.api.service.AsyncNeo4jSyncService;
import com.hcsy.spring.common.utils.UserContext;
import com.hcsy.spring.core.annotation.Neo4jSync;

import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;
import reactor.util.context.Context;

@Aspect
@Component
@RequiredArgsConstructor
public class Neo4jSyncAspect {

    private final AsyncNeo4jSyncService asyncNeo4jSyncService;

    @Around("@annotation(neo4jSync)")
    public Object handleNeo4jSync(ProceedingJoinPoint joinPoint, Neo4jSync neo4jSync) throws Throwable {
        Object result = joinPoint.proceed();
        String description = neo4jSync.description();

        if (result instanceof Mono<?> monoResult) {
            // 使用 doOnSuccess 发后即忘：主流程不等待 Neo4j 同步完成
            return Mono.deferContextual(ctx -> {
                Long userId = UserContext.getUserId(ctx);
                String username = UserContext.getUsername(ctx);
                Context syncContext = UserContext.writeContext(Context.empty(), userId, username, null, null, null);
                return monoResult
                    .doOnSuccess(value -> triggerNeo4jSync(joinPoint, description, userId, username)
                        .contextWrite(syncContext)
                        .subscribe());
            });
        }
        return result;
    }

    private Mono<Void> triggerNeo4jSync(ProceedingJoinPoint joinPoint, String description,
        Long userId, String username) {
        return asyncNeo4jSyncService.syncNeo4jAsync(
            joinPoint.getSignature().toShortString(),
            description);
    }
}
