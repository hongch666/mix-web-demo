package com.hcsy.spring.aop;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.aspectj.lang.annotation.*;
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.springframework.stereotype.Component;

import com.hcsy.spring.client.GinClient;

@Slf4j
@Aspect
@Component
@RequiredArgsConstructor
public class ArticleServiceAspect {

    private final GinClient ginClient;

    @Pointcut("execution(* com.hcsy.spring.service.ArticleService.saveArticle(..)) ||" +
            "execution(* com.hcsy.spring.service.ArticleService.updateArticle(..)) || " +
            "execution(* com.hcsy.spring.service.ArticleService.deleteArticle(..))")
    public void userServiceTargetMethods() {
    }

    @Around("userServiceTargetMethods()")
    public Object afterUserServiceMethod(ProceedingJoinPoint joinPoint) throws Throwable {
        // 执行原方法
        Object result = joinPoint.proceed();

        // 追加统一逻辑
        log.info("同步文章表到ES");
        ginClient.syncES();

        return result;
    }
}
