package com.hcsy.spring.core.aspect;

import java.util.Arrays;
import java.util.Collection;
import java.util.List;

import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.reflect.MethodSignature;

import com.hcsy.spring.common.constants.SyncChangeType;
import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.entity.event.ChangeEvent;

/**
 * 变更事件采集工具
 * 从切点入参与业务返回值中解析受影响的主键，兼容 DTO、主键、主键集合与逗号分隔字符串
 * 仅供同步切面使用，与切面同包避免把 AspectJ 依赖下沉到 common
 */
public final class SyncEventCollector {

    private SyncEventCollector() {
    }

    /**
     * 构建变更事件
     * 新增场景优先取业务返回值中的主键，取不到时退回入参解析
     */
    public static ChangeEvent collect(
        String resource,
        SyncChangeType changeType,
        Object primaryParam,
        Object result) {
        List<Long> ids = resolveIds(changeType, primaryParam, result);
        return ChangeEvent.of(resource, changeType, ids, "");
    }

    public static List<Long> resolveIds(SyncChangeType changeType, Object primaryParam, Object result) {
        if (changeType == SyncChangeType.INSERT) {
            List<Long> fromResult = readIdsFromResult(result);
            if (!fromResult.isEmpty()) {
                return fromResult;
            }
        }
        List<Long> fromParam = readIds(primaryParam);
        if (!fromParam.isEmpty()) {
            return fromParam;
        }
        return readIdsFromResult(result);
    }

    /**
     * 从业务返回值的 data 中解析主键
     */
    public static List<Long> readIdsFromResult(Object result) {
        if (result instanceof Result<?> businessResult) {
            return readIds(businessResult.getData());
        }
        return List.of();
    }

    /**
     * 解析受影响主键，兼容单个主键、主键集合、逗号分隔字符串与携带 id 属性的对象
     */
    public static List<Long> readIds(Object target) {
        if (target == null) {
            return List.of();
        }
        if (target instanceof Number number) {
            return List.of(number.longValue());
        }
        if (target instanceof Collection<?> collection) {
            return collection.stream()
                .filter(Number.class::isInstance)
                .map(item -> ((Number) item).longValue())
                .toList();
        }
        if (target instanceof String text) {
            if (text.isBlank()) {
                return List.of();
            }
            return Arrays.stream(text.split(","))
                .map(String::trim)
                .filter(item -> !item.isEmpty())
                .map(SyncEventCollector::parseLongSafely)
                .filter(item -> item != null)
                .toList();
        }
        Long id = readLong(target, "id");
        return id == null ? List.of() : List.of(id);
    }

    /**
     * 按属性名读取对象值，兼容控制器入参的 DTO 与实体
     */
    public static Object readProperty(Object target, String property) {
        if (target == null) {
            return null;
        }
        try {
            String getterName = "get" + Character.toUpperCase(property.charAt(0)) + property.substring(1);
            return target.getClass().getMethod(getterName).invoke(target);
        } catch (ReflectiveOperationException e) {
            return null;
        }
    }

    public static Long readLong(Object target, String property) {
        Object value = readProperty(target, property);
        return value instanceof Number number ? number.longValue() : null;
    }

    public static String readString(Object target, String property) {
        Object value = readProperty(target, property);
        return value instanceof String text ? text : null;
    }

    /**
     * 按方法参数名解析指定参数值，用于路径变量与多参数场景
     */
    public static Long readByName(ProceedingJoinPoint joinPoint, String parameterName) {
        String[] parameterNames = ((MethodSignature) joinPoint.getSignature()).getParameterNames();
        Object[] parameterValues = joinPoint.getArgs();
        if (parameterNames == null) {
            return null;
        }
        for (int index = 0; index < parameterNames.length && index < parameterValues.length; index++) {
            if (parameterName.equals(parameterNames[index])) {
                Object value = parameterValues[index];
                return value instanceof Number number ? number.longValue() : null;
            }
        }
        return null;
    }

    private static Long parseLongSafely(String value) {
        try {
            return Long.valueOf(value);
        } catch (NumberFormatException e) {
            return null;
        }
    }
}
