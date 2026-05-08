package com.hcsy.spring.core.aspect;

import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.springframework.stereotype.Component;
import org.springframework.transaction.support.TransactionSynchronization;
import org.springframework.transaction.support.TransactionSynchronizationManager;

import com.hcsy.spring.core.annotation.Neo4jSync;
import com.hcsy.spring.api.service.AsyncNeo4jSyncService;

import lombok.RequiredArgsConstructor;

@Aspect
@Component
@RequiredArgsConstructor
public class Neo4jSyncAspect {

    private final AsyncNeo4jSyncService asyncNeo4jSyncService;

    @Around("@annotation(neo4jSync)")
    public Object handleNeo4jSync(ProceedingJoinPoint joinPoint, Neo4jSync neo4jSync) throws Throwable {
        Object result = joinPoint.proceed();
        String description = neo4jSync.description();

        Runnable syncTask = () -> asyncNeo4jSyncService.syncNeo4jAsync(
                joinPoint.getSignature().toShortString(),
                description);

        if (TransactionSynchronizationManager.isSynchronizationActive()) {
            TransactionSynchronizationManager.registerSynchronization(new TransactionSynchronization() {
                @Override
                public void afterCommit() {
                    syncTask.run();
                }
            });
        } else {
            syncTask.run();
        }

        return result;
    }
}
