package com.hcsy.spring.core.aspect;

import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.springframework.stereotype.Component;

import com.hcsy.spring.api.service.AsyncSyncService;
import com.hcsy.spring.common.utils.UserContext;
import com.hcsy.spring.core.annotation.DataSync;

import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;
import reactor.util.context.Context;

/**
 * 数据同步切面
 * 在标注 @DataSync 的方法成功后并行触发 Neo4j 图谱同步与 ClickHouse 数仓同步，失败只记日志不影响主流程
 */
@Aspect
@Component
@RequiredArgsConstructor
public class DataSyncAspect {

    private final AsyncSyncService asyncSyncService;

    @Around("@annotation(dataSync)")
    public Object handleDataSync(ProceedingJoinPoint joinPoint, DataSync dataSync) throws Throwable {
        Object result = joinPoint.proceed();
        String description = dataSync.description();

        if (result instanceof Mono<?> monoResult) {
            // 使用 doOnSuccess 发后即忘：主流程不等待图谱与数仓同步完成
            return Mono.deferContextual(ctx -> {
                Long userId = UserContext.getUserId(ctx);
                String username = UserContext.getUsername(ctx);
                Context syncContext = UserContext.writeContext(Context.empty(), userId, username, null, null, null);
                return monoResult.doOnSuccess(value -> triggerSync(joinPoint, description, userId, username)
                    .contextWrite(syncContext)
                    .subscribe());
            });
        }
        return result;
    }

    /**
     * 并行触发图谱同步与数仓同步
     * 两个同步服务各自记录失败日志，此处吞掉异常避免影响主流程
     */
    private Mono<Void> triggerSync(ProceedingJoinPoint joinPoint, String description,
        Long userId, String username) {
        return Mono.whenDelayError(
            asyncSyncService.syncNeo4jAsync(joinPoint.getSignature().toShortString(), description),
            asyncSyncService.syncWarehouseAsync(userId, username))
            .onErrorResume(error -> Mono.empty());
    }
}
