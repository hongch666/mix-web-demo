package com.hcsy.spring.application.sync.aspect;

import java.lang.annotation.Annotation;

import org.aspectj.lang.ProceedingJoinPoint;

import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.common.utils.UserContext;

import reactor.core.publisher.Mono;
import reactor.util.context.Context;

/**
 * 同步切面公共骨架
 * 统一处理响应式上下文取用户身份、业务结果判定与发后即忘触发
 * 子类只实现 trigger，负责把注解与业务结果翻译成具体同步动作
 */
public abstract class AbstractSyncAspect<A extends Annotation> {

    /**
     * 执行具体同步动作，调用方保证只在业务成功后触发
     */
    protected abstract Mono<Void> trigger(
        ProceedingJoinPoint joinPoint, A annotation, Object result, Long userId, String username);

    /**
     * 环绕执行：业务 Mono 成功后触发同步，同步失败不影响主流程
     */
    protected Object aroundSync(ProceedingJoinPoint joinPoint, A annotation) throws Throwable {
        Object result = joinPoint.proceed();
        if (!(result instanceof Mono<?> monoResult)) {
            return result;
        }
        return Mono.deferContextual(ctx -> {
            Long userId = UserContext.getUserId(ctx);
            String username = UserContext.getUsername(ctx);
            Context syncContext = UserContext.writeContext(Context.empty(), userId, username, null, null, null);
            return monoResult.doOnSuccess(value -> {
                if (isBusinessSuccess(value)) {
                    trigger(joinPoint, annotation, value, userId, username)
                        .contextWrite(syncContext)
                        .subscribe();
                }
            });
        });
    }

    /**
     * 判断业务结果是否成功，只有真正发生数据变更才触发同步
     * 控制器在业务失败时会返回携带错误码的 Result，这类结果不能触发同步
     */
    private boolean isBusinessSuccess(Object result) {
        if (result instanceof Result<?> businessResult) {
            return businessResult.getCode() != null && businessResult.getCode() == HttpCode.OK;
        }
        return true;
    }
}
