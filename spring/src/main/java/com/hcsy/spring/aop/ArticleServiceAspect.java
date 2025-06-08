package com.hcsy.spring.aop;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.aspectj.lang.annotation.*;

import java.util.HashMap;
import java.util.Map;

import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.reflect.MethodSignature;
import org.springframework.stereotype.Component;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.hcsy.spring.client.GinClient;
import com.hcsy.spring.mq.RabbitMQService;
import com.hcsy.spring.po.Article;

@Slf4j
@Aspect
@Component
@RequiredArgsConstructor
public class ArticleServiceAspect {

    private final GinClient ginClient;
    private final RabbitMQService rabbitMQService;
    private final ObjectMapper objectMapper;

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

        // 获取方法签名（包含方法名）
        MethodSignature methodSignature = (MethodSignature) joinPoint.getSignature();
        String methodName = methodSignature.getName(); // 方法名

        // 获取参数名与参数值
        String[] paramNames = methodSignature.getParameterNames(); // 参数名
        Object[] paramValues = joinPoint.getArgs(); // 参数值

        // 分类构造数据
        switch (methodName) {
            case "saveArticle": {
                Article article = (Article) paramValues[0];
                Map<String, Object> msg = new HashMap<>();
                msg.put("content", article);
                msg.put("user_id", 1); // TODO: 后续改为ThreadLocal中的值
                msg.put("article_id", article.getId());
                msg.put("action", "add");
                msg.put("msg", "创建了1篇文章");
                String json = objectMapper.writeValueAsString(msg);
                rabbitMQService.sendMessage("log-queue", json);
                log.info("发送到MQ：" + json);
            }
                break;
            case "updateArticle": {
                Article article = (Article) paramValues[0];
                Map<String, Object> msg = new HashMap<>();
                msg.put("content", article);
                msg.put("user_id", 1); // TODO: 后续改为ThreadLocal中的值
                msg.put("article_id", article.getId());
                msg.put("action", "edit");
                msg.put("msg", "编辑了1篇文章");
                String json = objectMapper.writeValueAsString(msg);
                rabbitMQService.sendMessage("log-queue", json);
                log.info("发送到MQ：" + json);
            }
                break;
            case "deleteArticle": {
                Long id = (Long) paramValues[0];
                Map<String, Object> msg = new HashMap<>();
                Map<String, Object> content = new HashMap<>();
                content.put("id", id);
                msg.put("content", content);
                msg.put("user_id", 1); // TODO: 后续改为ThreadLocal中的值
                msg.put("article_id", id);
                msg.put("action", "edit");
                msg.put("msg", "删除了1篇文章");
                String json = objectMapper.writeValueAsString(msg);
                rabbitMQService.sendMessage("log-queue", json);
                log.info("发送到MQ：" + json);
            }
                break;
            default: {
                log.error("出现AOP错误");
            }
                break;
        }
        return result;
    }
}
