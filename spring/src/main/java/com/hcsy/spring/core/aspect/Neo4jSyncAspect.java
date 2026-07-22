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
            return monoResult
                    .flatMap(value -> triggerNeo4jSync(joinPoint, description).thenReturn(value))
                    .switchIfEmpty(triggerNeo4jSync(joinPoint, description).then(Mono.empty()));
        }
        return result;
    }

    private Mono<Void> triggerNeo4jSync(ProceedingJoinPoint joinPoint, String description) {
        return asyncNeo4jSyncService.syncNeo4jAsync(
                joinPoint.getSignature().toShortString(),
                description);
    }
}
