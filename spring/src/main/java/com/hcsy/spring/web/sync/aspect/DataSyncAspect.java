package com.hcsy.spring.web.sync.aspect;

import java.util.Set;

import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;

import com.hcsy.spring.application.service.AsyncSyncService;
import com.hcsy.spring.common.utils.SyncEventCollector;
import com.hcsy.spring.entity.event.ChangeEvent;
import com.hcsy.spring.web.sync.annotation.DataSync;

import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;

/**
 * 数据同步切面
 * 在标注 @DataSync 的方法成功后并行触发 Neo4j 图谱同步与 ClickHouse 数仓同步，失败只记日志不影响主流程
 * 同步入参为精确变更事件，携带资源名、变更类型与受影响主键
 */
@Aspect
@Component
@Order(30)
@RequiredArgsConstructor
public class DataSyncAspect extends AbstractSyncAspect<DataSync> {

    private final AsyncSyncService asyncSyncService;

    /**
     * 环绕通知，在标注 @DataSync 的接口成功执行后触发数据同步流程
     */
    @Around("@annotation(dataSync)")
    public Object handleDataSync(ProceedingJoinPoint joinPoint, DataSync dataSync) throws Throwable {
        return aroundSync(joinPoint, dataSync);
    }

    /**
     * 从入参与返回值采集携带资源名、变更类型与主键的精确变更事件，并行触发Neo4j图谱同步与数仓同步，失败仅记录日志
     */
    @Override
    protected Mono<Void> trigger(ProceedingJoinPoint joinPoint, DataSync dataSync, Object result,
        Long userId, String username) {
        String resource = dataSync.resource();
        Object[] paramValues = joinPoint.getArgs();
        Object primaryParam = paramValues != null && paramValues.length > 0 ? paramValues[0] : null;

        ChangeEvent event = SyncEventCollector.collect(resource, dataSync.changeType(), primaryParam, result);
        event.setTriggerUserId(userId);
        event.setTriggerUsername(username);

        Set<String> resources = resource.isBlank() ? Set.of() : Set.of(resource);
        return Mono.whenDelayError(
            asyncSyncService.syncNeo4jAsync(joinPoint.getSignature().toShortString(), dataSync.description(), event),
            asyncSyncService.syncWarehouseAsync(userId, username, resources))
            .onErrorResume(error -> Mono.empty());
    }
}
