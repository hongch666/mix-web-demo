package com.hcsy.spring.aop;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.aspectj.lang.annotation.*;

import java.util.HashMap;
import java.util.Map;

import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.reflect.MethodSignature;
import org.springframework.stereotype.Component;
import org.springframework.transaction.support.TransactionSynchronization;
import org.springframework.transaction.support.TransactionSynchronizationManager;
import org.springframework.transaction.support.TransactionTemplate;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.hcsy.spring.client.GinClient;
import com.hcsy.spring.mq.RabbitMQService;
import com.hcsy.spring.po.Article;
import com.hcsy.spring.utils.UserContext;

@Slf4j
@Aspect
@Component
@RequiredArgsConstructor
public class ArticleServiceAspect {

    private final GinClient ginClient;
    private final RabbitMQService rabbitMQService;
    private final ObjectMapper objectMapper;
    private final TransactionTemplate transactionTemplate;

    @Pointcut("execution(* com.hcsy.spring.service.ArticleService.saveArticle(..)) ||" +
            "execution(* com.hcsy.spring.service.ArticleService.updateArticle(..)) || " +
            "execution(* com.hcsy.spring.service.ArticleService.deleteArticle(..)) || " +
            "execution(* com.hcsy.spring.service.ArticleService.publishArticle(..)) || " +
            "execution(* com.hcsy.spring.service.ArticleService.addViewArticle(..))")
    public void userServiceTargetMethods() {
    }

    @Around("userServiceTargetMethods()")
    public Object afterUserServiceMethod(ProceedingJoinPoint joinPoint) throws Throwable {
        return transactionTemplate.execute(status -> {
            try {
                // 1. 执行业务方法（写数据库）
                Object result = joinPoint.proceed();

                // 2. 构建 MQ 消息
                MethodSignature methodSignature = (MethodSignature) joinPoint.getSignature();
                String methodName = methodSignature.getName();
                Object[] paramValues = joinPoint.getArgs();

                Map<String, Object> msg = new HashMap<>();
                String json = "";

                // 3. 获取当前用户 ID
                Long userId = UserContext.getUserId();
                if (userId == null) {
                    log.error("未登录，无法记录操作日志");
                    throw new RuntimeException("未登录，无法记录操作日志");
                }

                switch (methodName) {
                    case "saveArticle": {
                        Article article = (Article) paramValues[0];
                        msg.put("content", article);
                        msg.put("user_id", userId);
                        msg.put("article_id", article.getId());
                        msg.put("action", "add");
                        msg.put("msg", "创建了1篇文章");
                        json = objectMapper.writeValueAsString(msg);
                        break;
                    }
                    case "updateArticle": {
                        Article article = (Article) paramValues[0];
                        msg.put("content", article);
                        msg.put("user_id", userId);
                        msg.put("article_id", article.getId());
                        msg.put("action", "edit");
                        msg.put("msg", "编辑了1篇文章");
                        json = objectMapper.writeValueAsString(msg);
                        break;
                    }
                    case "deleteArticle": {
                        Long id = (Long) paramValues[0];
                        Map<String, Object> content = new HashMap<>();
                        content.put("id", id);
                        msg.put("content", content);
                        msg.put("user_id", userId);
                        msg.put("article_id", id);
                        msg.put("action", "edit");
                        msg.put("msg", "删除了1篇文章");
                        json = objectMapper.writeValueAsString(msg);
                        break;
                    }
                    case "publishArticle": {
                        Long id = (Long) paramValues[0];
                        Map<String, Object> content = new HashMap<>();
                        content.put("id", id);
                        msg.put("content", content);
                        msg.put("user_id", userId);
                        msg.put("article_id", id);
                        msg.put("action", "edit");
                        msg.put("msg", "发布了1篇文章");
                        json = objectMapper.writeValueAsString(msg);
                        break;
                    }
                    case "addViewArticle": {
                        Long id = (Long) paramValues[0];
                        Map<String, Object> content = new HashMap<>();
                        content.put("id", id);
                        msg.put("content", content);
                        msg.put("user_id", userId);
                        msg.put("article_id", id);
                        msg.put("action", "edit");
                        msg.put("msg", "浏览了1篇文章");
                        json = objectMapper.writeValueAsString(msg);
                        break;
                    }
                    default:
                        log.error("未知方法类型：" + methodName);
                        throw new RuntimeException("AOP识别失败");
                }

                // 3. 发消息
                rabbitMQService.sendMessage("log-queue", json);
                log.info("发送到MQ：" + json);

                // 4. 注册事务提交后的回调，同步 ES
                TransactionSynchronizationManager.registerSynchronization(new TransactionSynchronization() {
                    @Override
                    public void afterCommit() {
                        log.info("事务提交后开始同步ES...");
                        ginClient.syncES();
                    }
                });

                return result;

            } catch (Throwable e) {
                log.error("事务执行失败，已回滚", e);
                status.setRollbackOnly(); // 显式回滚
                throw new RuntimeException(e);
            }
        });
    }
}
