package com.hcsy.spring.core.aspect;

import java.util.Set;

import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.springframework.stereotype.Component;

import com.hcsy.spring.api.service.AsyncSyncService;
import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.constants.SyncChangeType;
import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.common.utils.SyncEventCollector;
import com.hcsy.spring.common.utils.UserContext;
import com.hcsy.spring.core.annotation.DataSync;
import com.hcsy.spring.entity.event.ChangeEvent;

import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;
import reactor.util.context.Context;

/**
 * 数据同步切面
 * 在标注 @DataSync 的方法成功后并行触发 Neo4j 图谱同步与 ClickHouse 数仓同步，失败只记日志不影响主流程
 * 同步入参为精确变更事件，携带资源名、变更类型与受影响主键
 */
@Aspect
@Component
@RequiredArgsConstructor
public class DataSyncAspect {

    private final AsyncSyncService asyncSyncService;

    @Around("@annotation(dataSync)")
    public Object handleDataSync(ProceedingJoinPoint joinPoint, DataSync dataSync) throws Throwable {
        Object result = joinPoint.proceed();
        if (result instanceof Mono<?> monoResult) {
            // 使用 doOnSuccess 发后即忘：主流程不等待图谱与数仓同步完成
            return Mono.deferContextual(ctx -> {
                Long userId = UserContext.getUserId(ctx);
                String username = UserContext.getUsername(ctx);
                Context syncContext = UserContext.writeContext(Context.empty(), userId, username, null, null, null);
                return monoResult.doOnSuccess(value -> {
                    if (isBusinessSuccess(value)) {
                        triggerSync(joinPoint, dataSync, userId, username, value)
                            .contextWrite(syncContext)
                            .subscribe();
                    }
                });
            });
        }
        return result;
    }

    private boolean isBusinessSuccess(Object result) {
        if (result instanceof Result<?> businessResult) {
            return businessResult.getCode() != null && businessResult.getCode() == HttpCode.OK;
        }
        return true;
    }

    /**
     * 并行触发图谱同步与数仓同步
     * 两个同步服务各自记录失败日志，此处吞掉异常避免影响主流程
     */
    private Mono<Void> triggerSync(ProceedingJoinPoint joinPoint, DataSync dataSync,
        Long userId, String username, Object result) {
        String resource = dataSync.resource();
        SyncChangeType changeType = dataSync.changeType() == null ? SyncChangeType.UPDATE : dataSync.changeType();
        Object[] paramValues = joinPoint.getArgs();
        Object primaryParam = paramValues != null && paramValues.length > 0 ? paramValues[0] : null;

        ChangeEvent event = SyncEventCollector.collect(resource, changeType, primaryParam, result);
        event.setTriggerUserId(userId);
        event.setTriggerUsername(username);

        Set<String> resources = resource == null || resource.isBlank() ? Set.of() : Set.of(resource);
        return Mono.whenDelayError(
            asyncSyncService.syncNeo4jAsync(joinPoint.getSignature().toShortString(), dataSync.description(), event),
            asyncSyncService.syncWarehouseAsync(userId, username, resources))
            .onErrorResume(error -> Mono.empty());
    }
}
