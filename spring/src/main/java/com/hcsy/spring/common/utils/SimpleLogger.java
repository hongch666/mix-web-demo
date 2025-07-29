package com.hcsy.spring.common.utils;

import org.springframework.stereotype.Component;

/**
 * 简单日志记录器，模仿 Python 的使用方式
 */
@Component
public class SimpleLogger {

    public void info(String message) {
        LoggerUtil.logInfo(message);
    }

    public void error(String message) {
        LoggerUtil.logError(message);
    }

    public void warning(String message) {
        LoggerUtil.logWarning(message);
    }

    public void debug(String message) {
        LoggerUtil.logDebug(message);
    }

    // 支持格式化字符串
    public void info(String format, Object... args) {
        String message = String.format(format, args);
        LoggerUtil.logInfo(message);
    }

    public void error(String format, Object... args) {
        String message = String.format(format, args);
        LoggerUtil.logError(message);
    }

    public void warning(String format, Object... args) {
        String message = String.format(format, args);
        LoggerUtil.logWarning(message);
    }

    public void debug(String format, Object... args) {
        String message = String.format(format, args);
        LoggerUtil.logDebug(message);
    }
}