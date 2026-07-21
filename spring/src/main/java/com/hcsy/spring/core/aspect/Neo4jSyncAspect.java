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
            // Controller 层返回 Mono 的方法
            return monoResult
                .doOnSuccess(res -> triggerNeo4jSync(joinPoint, description));
        }

        // Service 层返回非 Mono 类型的方法（boolean/Long/void 等）
        triggerNeo4jSync(joinPoint, description);
        return result;
    }

    private void triggerNeo4jSync(ProceedingJoinPoint joinPoint, String description) {
        asyncNeo4jSyncService.syncNeo4jAsync(
                joinPoint.getSignature().toShortString(),
                description);
    }
}
