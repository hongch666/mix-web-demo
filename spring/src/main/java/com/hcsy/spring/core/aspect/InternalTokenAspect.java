package com.hcsy.spring.core.aspect;

import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.springframework.stereotype.Component;

import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.exceptions.BusinessException;
import com.hcsy.spring.common.utils.InternalTokenUtil;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.common.utils.UserContext;
import com.hcsy.spring.core.annotation.RequireInternalToken;

import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;

/**
 * 内部服务令牌验证切面
 * 用于验证带有 @RequireInternalToken 注解的方法的请求令牌
 *
 * @author hcsy
 */
@Aspect
@Component
@RequiredArgsConstructor
public class InternalTokenAspect {

    private final InternalTokenUtil internalTokenUtil;
    private final SimpleLogger logger;

    /**
     * 环绕切面：在执行带有 @RequireInternalToken 注解的方法前验证内部令牌
     */
    @Around("@annotation(requireInternalToken)")
    public Object validateInternalToken(ProceedingJoinPoint pjp, RequireInternalToken requireInternalToken) throws Throwable {
        Object result = pjp.proceed();
        if (result instanceof Mono<?> monoResult) {
            return Mono.deferContextual(ctx -> validate(ctx, pjp, requireInternalToken).then(monoResult));
        }
        return result;
    }

    private Mono<Void> validate(reactor.util.context.ContextView ctx, ProceedingJoinPoint pjp,
            RequireInternalToken requireInternalToken) {
        try {
            String internalToken = UserContext.getInternalToken(ctx);
            if (internalToken == null || internalToken.isEmpty()) {
                logger.error(Messages.INTERNAL_TOKEN_MISSING);
                return Mono.error(BusinessException.builder().httpStatus(HttpCode.UNAUTHORIZED)
                        .errorMessage(Messages.INTERNAL_TOKEN_MISSING).build());
            }
            internalTokenUtil.validateInternalToken(internalToken);
            String requiredServiceName = requireInternalToken.value();
            if (requiredServiceName != null && !requiredServiceName.isEmpty()) {
                String tokenServiceName = internalTokenUtil.extractServiceName(internalToken);
                if (!requiredServiceName.equals(tokenServiceName)) {
                    logger.error(Messages.SERVICE_NAME_MISMATCH + ". 期望: " + requiredServiceName + ", 获得: "
                            + tokenServiceName);
                    return Mono.error(BusinessException.builder().httpStatus(HttpCode.FORBIDDEN)
                            .errorMessage(Messages.SERVICE_NAME_MISMATCH).build());
                }
            }
            logger.debug(Messages.INTERNAL_TOKEN_VALIDATE_METHOD + pjp.getSignature().getName());
            return Mono.empty();
        } catch (BusinessException error) {
            return Mono.error(error);
        } catch (Exception error) {
            logger.error(Messages.INTERNAL_TOKEN_VALIDATION_FAIL + error.getMessage(), error);
            return Mono.error(BusinessException.builder().httpStatus(HttpCode.UNAUTHORIZED)
                    .errorMessage(Messages.INTERNAL_TOKEN_VALIDATION_FAIL + error.getMessage()).build());
        }
    }
}
