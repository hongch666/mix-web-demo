package com.hcsy.spring.common.aspect;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.hcsy.spring.common.annotation.ApiLog;
import com.hcsy.spring.common.utils.Constants;
import com.hcsy.spring.common.utils.RabbitMQUtil;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.common.utils.UserContext;
import lombok.RequiredArgsConstructor;
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.JoinPoint;
import org.aspectj.lang.annotation.Aspect;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.reflect.MethodSignature;
import org.springframework.stereotype.Component;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.context.request.RequestContextHolder;
import org.springframework.web.context.request.ServletRequestAttributes;

import java.lang.reflect.Method;
import java.lang.reflect.Parameter;
import java.util.*;

/**
 * API 日志切面
 * 自动记录带有 @ApiLog 注解的方法的请求日志
 * 
 * @author hcsy
 */
@Aspect
@Component("apiMsgLogAspect")
@RequiredArgsConstructor
public class ApiLogAspect {

    private final SimpleLogger logger;
    private final ObjectMapper objectMapper;
    private final RabbitMQUtil rabbitMQUtil;

    /**
     * 环绕切面：在执行带有 @ApiLog 注解的方法前记录日志，并在执行后输出耗时
     */
    @Around("@annotation(apiLog)")
    public Object logAround(ProceedingJoinPoint pjp, ApiLog apiLog) throws Throwable {
        long start = System.currentTimeMillis();
        Object result = null;
        try {
            // 获取用户信息
            Long userId = UserContext.getUserId();
            String username = UserContext.getUsername();

            // 增加判空
            if (userId == null) {
                userId = 0L;
            }
            if (username == null) {
                username = "unknown";
            }

            // 获取请求信息
            MethodSignature signature = (MethodSignature) pjp.getSignature();
            Method method = signature.getMethod();

            String httpMethod = getHttpMethod(method);
            String requestPath = getRequestPath(method);

            // 构建基础日志消息
            String baseMessage = String.format("用户%s:%s %s %s: %s",
                    userId, username, httpMethod, requestPath, apiLog.value());

            // 添加参数信息
            if (apiLog.includeParams()) {
                String paramsInfo = extractParamsInfo(pjp, apiLog.excludeFields());
                if (paramsInfo != null && !paramsInfo.isEmpty()) {
                    baseMessage += "\n" + paramsInfo;
                }
            }

            // 根据日志级别记录日志（方法开始时）
            switch (apiLog.level()) {
                case WARN:
                    logger.warning(baseMessage);
                    break;
                case ERROR:
                    logger.error(baseMessage);
                    break;
                default:
                    logger.info(baseMessage);
                    break;
            }

            // 执行原方法
            result = pjp.proceed();

            return result;

        } catch (Throwable t) {
            // 若方法抛出异常，仍然向上抛出，但先记录错误日志
            logger.error(Constants.API_EXCEPTION, t);
            throw t;
        } finally {
            // 计算并记录耗时（无论正常或异常都会执行）
            long end = System.currentTimeMillis();
            long responseTime = end - start;

            try {
                MethodSignature signature = (MethodSignature) pjp.getSignature();
                Method method = signature.getMethod();
                String httpMethod = getHttpMethod(method);
                String requestPath = getRequestPath(method);

                String timeMessage = String.format("%s %s 使用了%dms", httpMethod, requestPath, responseTime);
                logger.info(timeMessage);

                // 向消息队列发送 API 日志
                sendApiLogToQueue(
                        pjp,
                        httpMethod,
                        requestPath,
                        apiLog.value(),
                        responseTime,
                        apiLog.excludeFields());
            } catch (Exception e) {
                logger.error(Constants.TIME_FAIL, e);
            }
        }
    }

    /**
     * 获取 HTTP 方法
     */
    private String getHttpMethod(Method method) {
        if (method.isAnnotationPresent(GetMapping.class)) {
            return "GET";
        } else if (method.isAnnotationPresent(PostMapping.class)) {
            return "POST";
        } else if (method.isAnnotationPresent(PutMapping.class)) {
            return "PUT";
        } else if (method.isAnnotationPresent(DeleteMapping.class)) {
            return "DELETE";
        } else if (method.isAnnotationPresent(PatchMapping.class)) {
            return "PATCH";
        } else if (method.isAnnotationPresent(RequestMapping.class)) {
            RequestMapping requestMapping = method.getAnnotation(RequestMapping.class);
            RequestMethod[] requestMethods = requestMapping.method();
            if (requestMethods.length > 0) {
                return requestMethods[0].name();
            }
        }
        return "UNKNOWN";
    }

    /**
     * 获取请求路径
     */
    private String getRequestPath(Method method) {
        String classPath = getClassRequestPath(method.getDeclaringClass());
        String methodPath = getMethodRequestPath(method);

        return classPath + methodPath;
    }

    /**
     * 获取类级别的请求路径
     */
    private String getClassRequestPath(Class<?> clazz) {
        if (clazz.isAnnotationPresent(RequestMapping.class)) {
            RequestMapping requestMapping = clazz.getAnnotation(RequestMapping.class);
            String[] paths = requestMapping.value();
            if (paths.length > 0) {
                return paths[0];
            }
        }
        return "";
    }

    /**
     * 获取方法级别的请求路径
     */
    private String getMethodRequestPath(Method method) {
        // 检查各种映射注解
        if (method.isAnnotationPresent(GetMapping.class)) {
            return getPathFromAnnotation(method.getAnnotation(GetMapping.class).value());
        } else if (method.isAnnotationPresent(PostMapping.class)) {
            return getPathFromAnnotation(method.getAnnotation(PostMapping.class).value());
        } else if (method.isAnnotationPresent(PutMapping.class)) {
            return getPathFromAnnotation(method.getAnnotation(PutMapping.class).value());
        } else if (method.isAnnotationPresent(DeleteMapping.class)) {
            return getPathFromAnnotation(method.getAnnotation(DeleteMapping.class).value());
        } else if (method.isAnnotationPresent(PatchMapping.class)) {
            return getPathFromAnnotation(method.getAnnotation(PatchMapping.class).value());
        } else if (method.isAnnotationPresent(RequestMapping.class)) {
            return getPathFromAnnotation(method.getAnnotation(RequestMapping.class).value());
        }
        return "";
    }

    /**
     * 从注解值数组中获取路径
     */
    private String getPathFromAnnotation(String[] paths) {
        if (paths.length > 0) {
            return paths[0];
        }
        return "";
    }

    /**
     * 提取参数信息
     */
    private String extractParamsInfo(JoinPoint joinPoint, String[] excludeFields) {
        try {
            MethodSignature signature = (MethodSignature) joinPoint.getSignature();
            Method method = signature.getMethod();
            Parameter[] parameters = method.getParameters();
            Object[] args = joinPoint.getArgs();

            List<String> paramInfoList = new ArrayList<>();
            Set<String> excludeSet = new HashSet<>(Arrays.asList(excludeFields));

            for (int i = 0; i < parameters.length && i < args.length; i++) {
                Parameter parameter = parameters[i];
                Object arg = args[i];

                if (arg == null)
                    continue;

                // 获取参数名称和值
                String paramName = getParameterName(parameter, arg);
                String paramValue = formatParameterValue(arg, excludeSet);

                if (paramName != null && paramValue != null) {
                    paramInfoList.add(paramName + ": " + paramValue);
                }
            }

            return String.join("\n", paramInfoList);

        } catch (Exception e) {
            logger.error(Constants.PARAM_EXPIRED, e);
            return Constants.PARAM_EXPIRED;
        }
    }

    /**
     * 获取参数名称
     */
    private String getParameterName(Parameter parameter, Object arg) {
        // 检查参数注解
        if (parameter.isAnnotationPresent(RequestBody.class)) {
            return getClassSimpleName(arg.getClass());
        } else if (parameter.isAnnotationPresent(PathVariable.class)) {
            PathVariable pathVariable = parameter.getAnnotation(PathVariable.class);
            String name = pathVariable.value().isEmpty() ? pathVariable.name() : pathVariable.value();
            return name.isEmpty() ? parameter.getName().toUpperCase() : name.toUpperCase();
        } else if (parameter.isAnnotationPresent(RequestParam.class)) {
            RequestParam requestParam = parameter.getAnnotation(RequestParam.class);
            String name = requestParam.value().isEmpty() ? requestParam.name() : requestParam.value();
            return name.isEmpty() ? parameter.getName() : name;
        }

        // 默认返回参数类型名称
        return getClassSimpleName(arg.getClass());
    }

    /**
     * 获取类的简单名称（用于DTO等）
     */
    private String getClassSimpleName(Class<?> clazz) {
        String simpleName = clazz.getSimpleName();

        // 如果是DTO类，返回DTO名称
        if (simpleName.endsWith("DTO")) {
            return simpleName;
        } else if (simpleName.endsWith("Request")) {
            return simpleName;
        } else if (simpleName.endsWith("Param")) {
            return simpleName;
        }

        return simpleName;
    }

    /**
     * 格式化参数值
     */
    private String formatParameterValue(Object arg, Set<String> excludeFields) {
        try {
            if (arg == null) {
                return "null";
            }

            // 基础类型直接返回字符串
            if (isPrimitiveOrWrapper(arg.getClass()) || arg instanceof String) {
                return arg.toString();
            }

            // 集合类型
            if (arg instanceof Collection || arg.getClass().isArray()) {
                return objectMapper.writeValueAsString(arg);
            }

            // 复杂对象类型，需要过滤敏感字段
            if (!excludeFields.isEmpty()) {
                Map<String, Object> filteredMap = objectToMap(arg, excludeFields);
                return objectMapper.writeValueAsString(filteredMap);
            } else {
                return objectMapper.writeValueAsString(arg);
            }

        } catch (JsonProcessingException e) {
            logger.error(Constants.FORMAT_PARAM, e);
            return arg.getClass().getSimpleName();
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
     * 将对象转换为 Map 并过滤敏感字段
     */
    @SuppressWarnings("unchecked")
    private Map<String, Object> objectToMap(Object obj, Set<String> excludeFields) {
        try {
            Map<String, Object> map = objectMapper.convertValue(obj, Map.class);
            Map<String, Object> filteredMap = new HashMap<>();

            for (Map.Entry<String, Object> entry : map.entrySet()) {
                if (!excludeFields.contains(entry.getKey())) {
                    filteredMap.put(entry.getKey(), entry.getValue());
                }
            }

            return filteredMap;
        } catch (Exception e) {
            logger.error(Constants.OBJECT_TO_MAP, e);
            return Collections.emptyMap();
        }
    }

    /**
     * 向消息队列发送 API 日志
     * 在接口完成后自动发送到 RabbitMQ
     */
    private void sendApiLogToQueue(
            ProceedingJoinPoint pjp,
            String httpMethod,
            String requestPath,
            String description,
            long responseTime,
            String[] excludeFields) {
        try {
            // 获取用户信息
            Long userId = UserContext.getUserId();
            if (userId == null) {
                userId = 0L;
            }
            String username = UserContext.getUsername();
            if (username == null) {
                username = "unknown";
            }

            // 获取 HTTP 请求对象
            ServletRequestAttributes attributes = (ServletRequestAttributes) RequestContextHolder
                    .getRequestAttributes();

            Object queryParams = null;
            Object pathParams = null;
            Object requestBody = null;

            if (attributes != null) {
                // 提取查询参数（仅 GET 请求）
                if ("GET".equals(httpMethod)) {
                    java.util.Map<String, String[]> parameterMap = attributes.getRequest().getParameterMap();
                    if (!parameterMap.isEmpty()) {
                        queryParams = new HashMap<>(parameterMap);
                    }
                }

                // 提取路径参数 - 从 pjp 的参数中获取
                Map<String, Object> extractedPathParams = extractPathParams(pjp);
                if (!extractedPathParams.isEmpty()) {
                    pathParams = extractedPathParams;
                }
            }

            // 提取请求体（非 GET 请求）
            if (!"GET".equals(httpMethod)) {
                Set<String> excludeSet = new HashSet<>(Arrays.asList(excludeFields));
                requestBody = extractRequestBody(pjp, excludeSet);
            }

            // 构建消息对象（snake_case 格式匹配队列契约）
            Map<String, Object> apiLogMessage = new LinkedHashMap<>();
            apiLogMessage.put("user_id", userId);
            apiLogMessage.put("username", username);
            apiLogMessage.put("api_description", description);
            apiLogMessage.put("api_path", requestPath);
            apiLogMessage.put("api_method", httpMethod);
            apiLogMessage.put("query_params", queryParams);
            apiLogMessage.put("path_params", pathParams);
            apiLogMessage.put("request_body", requestBody);
            apiLogMessage.put("response_time", responseTime);

            // 发送到消息队列
            rabbitMQUtil.sendMessage("api-log-queue", apiLogMessage);

            logger.info(String.format(
                    Constants.RabbitMQ_SEND_SUCCESS,
                    objectMapper.writeValueAsString(apiLogMessage)));

        } catch (Exception e) {
            logger.error(Constants.RabbitMQ_SEND_FAIL + e.getMessage(), e);
            // 不要抛出异常，避免影响业务逻辑
        }
    }

    /**
     * 提取路径参数
     */
    private Map<String, Object> extractPathParams(ProceedingJoinPoint pjp) {
        Map<String, Object> pathParams = new HashMap<>();
        try {
            MethodSignature signature = (MethodSignature) pjp.getSignature();
            Method method = signature.getMethod();
            Parameter[] parameters = method.getParameters();
            Object[] args = pjp.getArgs();

            for (int i = 0; i < parameters.length && i < args.length; i++) {
                Parameter parameter = parameters[i];
                if (parameter.isAnnotationPresent(PathVariable.class)) {
                    PathVariable pathVariable = parameter.getAnnotation(PathVariable.class);
                    String name = pathVariable.value().isEmpty() ? pathVariable.name() : pathVariable.value();
                    String paramName = name.isEmpty() ? parameter.getName() : name;
                    pathParams.put(paramName, args[i]);
                }
            }
        } catch (Exception e) {
            logger.error(Constants.PATH_PARAM, e);
        }
        return pathParams;
    }

    /**
     * 提取请求体
     */
    private Object extractRequestBody(ProceedingJoinPoint pjp, Set<String> excludeFields) {
        try {
            MethodSignature signature = (MethodSignature) pjp.getSignature();
            Method method = signature.getMethod();
            Parameter[] parameters = method.getParameters();
            Object[] args = pjp.getArgs();

            for (int i = 0; i < parameters.length && i < args.length; i++) {
                Parameter parameter = parameters[i];
                Object arg = args[i];

                if (arg == null) {
                    continue;
                }

                // 查找 @RequestBody 注解的参数
                if (parameter.isAnnotationPresent(RequestBody.class)) {
                    if (!excludeFields.isEmpty() && !isPrimitiveOrWrapper(arg.getClass())) {
                        // 过滤敏感字段
                        return objectToMap(arg, excludeFields);
                    }
                    return arg;
                }
            }
        } catch (Exception e) {
            logger.error(Constants.BODY_PARAM, e);
        }
        return null;
    }
}