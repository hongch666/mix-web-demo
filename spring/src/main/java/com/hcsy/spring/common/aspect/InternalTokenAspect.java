package com.hcsy.spring.common.aspect;

import com.hcsy.spring.common.annotation.RequireInternalToken;
import com.hcsy.spring.common.exceptions.BusinessException;
import com.hcsy.spring.common.utils.Constants;
import com.hcsy.spring.common.utils.InternalTokenUtil;
import com.hcsy.spring.common.utils.SimpleLogger;

import lombok.RequiredArgsConstructor;
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.springframework.stereotype.Component;
import org.springframework.web.context.request.RequestContextHolder;
import org.springframework.web.context.request.ServletRequestAttributes;

import jakarta.servlet.http.HttpServletRequest;

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

    private static final String INTERNAL_TOKEN_HEADER = "X-Internal-Token";
    private static final String BEARER_PREFIX = "Bearer ";

    /**
     * 环绕切面：在执行带有 @RequireInternalToken 注解的方法前验证内部令牌
     */
    @Around("@annotation(requireInternalToken)")
    public Object validateInternalToken(ProceedingJoinPoint pjp, RequireInternalToken requireInternalToken)
            throws Throwable {
        HttpServletRequest request = getCurrentRequest();
        String internalToken = extractInternalToken(request);

        if (internalToken == null || internalToken.isEmpty()) {
            logger.error(Constants.INTERNAL_TOKEN_MISSING);
            throw new BusinessException(Constants.INTERNAL_TOKEN_MISSING);
        }

        try {
            // 验证内部令牌
            internalTokenUtil.validateInternalToken(internalToken);

            // 验证服务名称（如果指定了）
            String requiredServiceName = requireInternalToken.value();
            if (requiredServiceName != null && !requiredServiceName.isEmpty()) {
                String tokenServiceName = internalTokenUtil.extractServiceName(internalToken);
                if (!requiredServiceName.equals(tokenServiceName)) {
                    logger.error(Constants.SERVICE_NAME_MISMATCH + ". 期望: " + requiredServiceName + ", 获得: "
                            + tokenServiceName);
                    throw new BusinessException(Constants.SERVICE_NAME_MISMATCH);
                }
            }

            logger.debug(Constants.INTERNAL_TOKEN_VALIDATE_METHOD + pjp.getSignature().getName());

            // 继续执行原方法
            return pjp.proceed();
        } catch (BusinessException e) {
            throw e;
        } catch (Exception e) {
            logger.error(Constants.INTERNAL_TOKEN_VALIDATION_FAIL + e.getMessage());
            throw new BusinessException(Constants.INTERNAL_TOKEN_VALIDATION_FAIL + e.getMessage());
        }
    }

    /**
     * 从请求头中提取内部令牌
     */
    private String extractInternalToken(HttpServletRequest request) {
        String authHeader = request.getHeader(INTERNAL_TOKEN_HEADER);
        if (authHeader != null && authHeader.startsWith(BEARER_PREFIX)) {
            return authHeader.substring(BEARER_PREFIX.length());
        }
        return authHeader;
    }

    /**
     * 获取当前HTTP请求
     */
    private HttpServletRequest getCurrentRequest() {
        ServletRequestAttributes attributes = (ServletRequestAttributes) RequestContextHolder.getRequestAttributes();
        if (attributes == null) {
            throw new BusinessException(Constants.CANNOT_GET_HTTP_REQUEST);
        }
        return attributes.getRequest();
    }
}
