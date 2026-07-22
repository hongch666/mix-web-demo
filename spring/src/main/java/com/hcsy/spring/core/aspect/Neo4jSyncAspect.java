package com.hcsy.spring.core.aspect;

import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.springframework.stereotype.Component;

import com.hcsy.spring.core.annotation.Neo4jSync;
import com.hcsy.spring.api.service.AsyncNeo4jSyncService;

import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;

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
            return monoResult
                    .doOnSuccess(value -> triggerNeo4jSync(joinPoint, description).subscribe());
        }
        return result;
    }

    private Mono<Void> triggerNeo4jSync(ProceedingJoinPoint joinPoint, String description) {
        return asyncNeo4jSyncService.syncNeo4jAsync(
                joinPoint.getSignature().toShortString(),
                description);
    }
}
