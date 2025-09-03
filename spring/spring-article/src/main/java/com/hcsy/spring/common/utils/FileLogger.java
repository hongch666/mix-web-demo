package com.hcsy.spring.common.utils;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import jakarta.annotation.PostConstruct;

/**
 * 全局文件日志器
 */
@Component
public class FileLogger {

    @Autowired
    private SimpleLogger simpleLogger;

    private static SimpleLogger fileLogger;

    @PostConstruct
    public void init() {
        fileLogger = this.simpleLogger;
    }

    public static SimpleLogger getInstance() {
        return fileLogger;
    }

    // 便捷的静态方法
    public static void info(String message) {
        if (fileLogger != null) {
            fileLogger.info(message);
        } else {
            LoggerUtil.logInfo(message);
        }
    }

    public static void error(String message) {
        if (fileLogger != null) {
            fileLogger.error(message);
        } else {
            LoggerUtil.logError(message);
        }
    }

    public static void warning(String message) {
        if (fileLogger != null) {
            fileLogger.warning(message);
        } else {
            LoggerUtil.logWarning(message);
        }
    }

    public static void debug(String message) {
        if (fileLogger != null) {
            fileLogger.debug(message);
        } else {
            LoggerUtil.logDebug(message);
        }
    }
}