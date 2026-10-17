package com.hcsy.spring.web.logging.aspect;

import java.lang.reflect.Method;
import java.lang.reflect.Parameter;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

import org.aspectj.lang.JoinPoint;
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.aspectj.lang.reflect.MethodSignature;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RequestParam;

import com.hcsy.spring.application.service.AsyncApiLogService;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.common.utils.UserContext;
import com.hcsy.spring.entity.event.ApiLogEvent;
import com.hcsy.spring.web.logging.annotation.ApiLog;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;
import reactor.util.context.ContextView;

/**
 * API 日志切面
 * 自动记录带有 @ApiLog 注解的方法的请求日志，成功与失败都会投递到接口日志队列
 *
 * @author hcsy
 */
@Aspect
@Component
@Order(0)
@RequiredArgsConstructor
public class ApiLogAspect {

    private static final String HTTP_GET = "GET";

    private final SimpleLogger logger;
    private final ObjectMapper objectMapper;
    private final AsyncApiLogService asyncApiLogService;

    /**
     * 环绕切面：进入方法前记录起始日志，方法结束后记录耗时并投递接口日志
     * 成功、空结果与异常都会投递，避免失败请求在日志平台中缺失
     */
    @Around("@annotation(apiLog)")
    public Object logAround(ProceedingJoinPoint pjp, ApiLog apiLog) throws Throwable {
        Method method = ((MethodSignature) pjp.getSignature()).getMethod();
        String httpMethod = resolveHttpMethod(method);
        String requestPath = resolveRequestPath(method);
        long start = System.currentTimeMillis();

        logStart(pjp, apiLog, httpMethod, requestPath);

        Object result = pjp.proceed();
        if (result instanceof Mono<?> monoResult) {
            return Mono.deferContextual(ctx -> monoResult
                .doOnSuccess(value -> report(ctx, pjp, apiLog, httpMethod, requestPath, start))
                .doOnError(error -> {
                    report(ctx, pjp, apiLog, httpMethod, requestPath, start);
                    logger.error(Messages.API_EXCEPTION + error.getMessage(), error);
                }));
        }

        // 非响应式类型保持原逻辑（如内部调用）
        return result;
    }

    private void logStart(ProceedingJoinPoint pjp, ApiLog apiLog, String httpMethod, String requestPath) {
        StringBuilder message = new StringBuilder(
            String.format(Messages.API_LOG_START, httpMethod, requestPath, apiLog.value()));
        if (apiLog.includeParams()) {
            String paramsInfo = extractParamsInfo(pjp, apiLog.excludeFields());
            if (!paramsInfo.isEmpty()) {
                message.append("\n").append(paramsInfo);
            }
        }
        switch (apiLog.level()) {
            case WARN -> logger.warning(message.toString());
            case ERROR -> logger.error(message.toString());
            default -> logger.info(message.toString());
        }
    }

    /**
     * 记录耗时并异步投递接口日志，投递失败不影响主流程
     */
    private void report(ContextView ctx, ProceedingJoinPoint pjp, ApiLog apiLog, String httpMethod,
        String requestPath, long start) {
        long duration = System.currentTimeMillis() - start;
        logger.info(String.format(Messages.API_LOG_DURATION, httpMethod, requestPath, duration));
        sendApiLogToQueue(ctx, pjp, apiLog, httpMethod, requestPath, duration).subscribe();
    }

    /**
     * 向消息队列发送接口日志
     */
    private Mono<Void> sendApiLogToQueue(ContextView ctx, ProceedingJoinPoint pjp, ApiLog apiLog,
        String httpMethod, String requestPath, long responseTime) {
        try {
            Long userId = UserContext.getUserId(ctx);
            String username = UserContext.getUsername(ctx);
            Set<String> excludeFields = new HashSet<>(Arrays.asList(apiLog.excludeFields()));
            Object requestBody = HTTP_GET.equals(httpMethod) ? null : extractRequestBody(pjp, excludeFields);
            Map<String, Object> pathParams = extractPathParams(pjp);

            ApiLogEvent event = ApiLogEvent.builder()
                .userId(userId == null ? 0L : userId)
                .username(username == null ? Messages.UNKNOWN_USERNAME : username)
                .apiDescription(apiLog.value())
                .apiPath(requestPath)
                .apiMethod(httpMethod)
                .pathParams(pathParams.isEmpty() ? null : pathParams)
                .requestBody(requestBody)
                .responseTime(responseTime)
                .build();
            return asyncApiLogService.sendAsync(event);
        } catch (Exception error) {
            logger.error(Messages.RabbitMQ_SEND_FAIL + error.getMessage(), error);
            return Mono.empty();
        }
    }

    /**
     * 解析 HTTP 方法
     */
    private String resolveHttpMethod(Method method) {
        if (method.isAnnotationPresent(GetMapping.class)) {
            return "GET";
        }
        if (method.isAnnotationPresent(PostMapping.class)) {
            return "POST";
        }
        if (method.isAnnotationPresent(PutMapping.class)) {
            return "PUT";
        }
        if (method.isAnnotationPresent(DeleteMapping.class)) {
            return "DELETE";
        }
        if (method.isAnnotationPresent(PatchMapping.class)) {
            return "PATCH";
        }
        if (method.isAnnotationPresent(RequestMapping.class)) {
            RequestMethod[] requestMethods = method.getAnnotation(RequestMapping.class).method();
            if (requestMethods.length > 0) {
                return requestMethods[0].name();
            }
        }
        return Messages.UNKNOWN_HTTP_METHOD;
    }

    /**
     * 解析接口路径，类路径与方法路径拼接时补齐分隔符
     */
    private String resolveRequestPath(Method method) {
        String classPath = firstPath(getClassPaths(method.getDeclaringClass()));
        String methodPath = firstPath(getMethodPaths(method));
        if (classPath.isEmpty()) {
            return withLeadingSlash(methodPath);
        }
        if (methodPath.isEmpty()) {
            return classPath;
        }
        String base = classPath.endsWith("/") ? classPath.substring(0, classPath.length() - 1) : classPath;
        return base + withLeadingSlash(methodPath);
    }

    private String[] getClassPaths(Class<?> clazz) {
        RequestMapping requestMapping = clazz.getAnnotation(RequestMapping.class);
        return requestMapping == null ? new String[0] : requestMapping.value();
    }

    private String[] getMethodPaths(Method method) {
        if (method.isAnnotationPresent(GetMapping.class)) {
            return method.getAnnotation(GetMapping.class).value();
        }
        if (method.isAnnotationPresent(PostMapping.class)) {
            return method.getAnnotation(PostMapping.class).value();
        }
        if (method.isAnnotationPresent(PutMapping.class)) {
            return method.getAnnotation(PutMapping.class).value();
        }
        if (method.isAnnotationPresent(DeleteMapping.class)) {
            return method.getAnnotation(DeleteMapping.class).value();
        }
        if (method.isAnnotationPresent(PatchMapping.class)) {
            return method.getAnnotation(PatchMapping.class).value();
        }
        if (method.isAnnotationPresent(RequestMapping.class)) {
            return method.getAnnotation(RequestMapping.class).value();
        }
        return new String[0];
    }

    private String firstPath(String[] paths) {
        return paths.length == 0 || paths[0] == null ? "" : paths[0].trim();
    }

    private String withLeadingSlash(String path) {
        if (path.isEmpty() || path.startsWith("/")) {
            return path;
        }
        return "/" + path;
    }

    /**
     * 提取参数信息
     */
    private String extractParamsInfo(JoinPoint joinPoint, String[] excludeFields) {
        try {
            Parameter[] parameters = ((MethodSignature) joinPoint.getSignature()).getMethod().getParameters();
            Object[] args = joinPoint.getArgs();
            Set<String> excludeSet = new HashSet<>(Arrays.asList(excludeFields));
            List<String> paramInfoList = new ArrayList<>();

            for (int index = 0; index < parameters.length && index < args.length; index++) {
                Object arg = args[index];
                if (arg == null) {
                    continue;
                }
                String paramName = getParameterName(parameters[index], arg);
                String paramValue = formatParameterValue(arg, excludeSet);
                if (paramName != null && paramValue != null) {
                    paramInfoList.add(paramName + ": " + paramValue);
                }
            }
            return String.join("\n", paramInfoList);
        } catch (Exception error) {
            logger.error(Messages.PARAM_EXPIRED, error);
            return Messages.PARAM_EXPIRED;
        }
    }

    /**
     * 获取参数名称
     */
    private String getParameterName(Parameter parameter, Object arg) {
        if (parameter.isAnnotationPresent(RequestBody.class)) {
            return arg.getClass().getSimpleName();
        }
        if (parameter.isAnnotationPresent(PathVariable.class)) {
            PathVariable pathVariable = parameter.getAnnotation(PathVariable.class);
            String name = pathVariable.value().isEmpty() ? pathVariable.name() : pathVariable.value();
            return name.isEmpty() ? parameter.getName().toUpperCase() : name.toUpperCase();
        }
        if (parameter.isAnnotationPresent(RequestParam.class)) {
            RequestParam requestParam = parameter.getAnnotation(RequestParam.class);
            String name = requestParam.value().isEmpty() ? requestParam.name() : requestParam.value();
            return name.isEmpty() ? parameter.getName() : name;
        }
        return arg.getClass().getSimpleName();
    }

    /**
     * 格式化参数值
     */
    private String formatParameterValue(Object arg, Set<String> excludeFields) {
        try {
            if (isPrimitiveOrWrapper(arg.getClass()) || arg instanceof String) {
                return arg.toString();
            }
            return objectMapper.writeValueAsString(toLoggable(arg, excludeFields));
        } catch (JsonProcessingException error) {
            logger.error(Messages.FORMAT_PARAM, error);
            return arg.getClass().getSimpleName();
        }
    }

    /**
     * 转为可序列化结构并剔除敏感字段，嵌套对象与数组一并处理
     */
    private Object toLoggable(Object arg, Set<String> excludeFields) {
        JsonNode node = objectMapper.valueToTree(arg);
        if (!excludeFields.isEmpty()) {
            stripSensitiveFields(node, excludeFields);
        }
        return node;
    }

    private void stripSensitiveFields(JsonNode node, Set<String> excludeFields) {
        if (node instanceof ObjectNode objectNode) {
            objectNode.remove(excludeFields);
            objectNode.fields().forEachRemaining(entry -> stripSensitiveFields(entry.getValue(), excludeFields));
        } else if (node instanceof ArrayNode arrayNode) {
            arrayNode.forEach(item -> stripSensitiveFields(item, excludeFields));
        }
    }

    /**
     * 判断是否为基础类型或包装类型
     */
    private boolean isPrimitiveOrWrapper(Class<?> clazz) {
        return clazz.isPrimitive() ||
            clazz == Boolean.class ||
            clazz == Byte.class ||
            clazz == Character.class ||
            clazz == Short.class ||
            clazz == Integer.class ||
            clazz == Long.class ||
            clazz == Float.class ||
            clazz == Double.class;
    }

    /**
     * 提取路径参数
     */
    private Map<String, Object> extractPathParams(ProceedingJoinPoint pjp) {
        Map<String, Object> pathParams = new LinkedHashMap<>();
        try {
            Parameter[] parameters = ((MethodSignature) pjp.getSignature()).getMethod().getParameters();
            Object[] args = pjp.getArgs();
            for (int index = 0; index < parameters.length && index < args.length; index++) {
                if (parameters[index].isAnnotationPresent(PathVariable.class)) {
                    PathVariable pathVariable = parameters[index].getAnnotation(PathVariable.class);
                    String name = pathVariable.value().isEmpty() ? pathVariable.name() : pathVariable.value();
                    pathParams.put(name.isEmpty() ? parameters[index].getName() : name, args[index]);
                }
            }
        } catch (Exception error) {
            logger.error(Messages.PATH_PARAM, error);
        }
        return pathParams;
    }

    /**
     * 提取请求体并剔除敏感字段，嵌套对象同样生效
     */
    private Object extractRequestBody(ProceedingJoinPoint pjp, Set<String> excludeFields) {
        try {
            Parameter[] parameters = ((MethodSignature) pjp.getSignature()).getMethod().getParameters();
            Object[] args = pjp.getArgs();
            for (int index = 0; index < parameters.length && index < args.length; index++) {
                Object arg = args[index];
                if (arg != null && parameters[index].isAnnotationPresent(RequestBody.class)) {
                    return toLoggable(arg, excludeFields);
                }
            }
        } catch (Exception error) {
            logger.error(Messages.BODY_PARAM, error);
        }
        return null;
    }
}
