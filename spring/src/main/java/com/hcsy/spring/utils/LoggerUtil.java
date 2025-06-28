package com.hcsy.spring.utils;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import jakarta.annotation.PostConstruct;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

@Component
public class LoggerUtil {

    private static final Logger logger = LoggerFactory.getLogger(LoggerUtil.class);
    private static final DateTimeFormatter DATE_FORMATTER = DateTimeFormatter.ofPattern("yyyy-MM-dd");
    private static final DateTimeFormatter TIMESTAMP_FORMATTER = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

    @Value("${logging.file.path:logs}")
    private String logPath;

    private static String staticLogPath;

    @PostConstruct
    public void init() {
        staticLogPath = this.logPath;
        // 创建日志目录
        File logDir = new File(staticLogPath);
        if (!logDir.exists()) {
            logDir.mkdirs();
        }
        logger.info("日志配置初始化完成，路径: {}", staticLogPath);
    }

    /**
     * 直接写入日志到文件
     * 
     * @param message 日志消息
     * @param level   日志级别
     */
    public static void writeLog(String message, String level) {
        if (staticLogPath == null) {
            staticLogPath = "logs"; // 默认路径
        }

        try {
            // 确保日志目录存在
            File logDir = new File(staticLogPath);
            if (!logDir.exists()) {
                logDir.mkdirs();
            }

            // 日志文件名 (按日期)
            String today = LocalDateTime.now().format(DATE_FORMATTER);
            String logFileName = String.format("app_%s.log", today);
            File logFile = new File(logDir, logFileName);

            // 格式化日志消息
            String timestamp = LocalDateTime.now().format(TIMESTAMP_FORMATTER);
            String logEntry = String.format("%s - %s - %s%n", timestamp, level, message);

            // 写入文件
            try (FileWriter writer = new FileWriter(logFile, true)) {
                writer.write(logEntry);
                writer.flush();
            }

        } catch (IOException e) {
            logger.error("写入日志失败: {}", e.getMessage(), e);
        }
    }

    // 便捷静态方法
    public static void logInfo(String message) {
        logger.info(message);
        writeLog(message, "INFO");
    }

    public static void logError(String message) {
        logger.error(message);
        writeLog(message, "ERROR");
    }

    public static void logWarning(String message) {
        logger.warn(message);
        writeLog(message, "WARNING");
    }

    public static void logDebug(String message) {
        logger.debug(message);
        writeLog(message, "DEBUG");
    }

    // 获取当前日志路径
    public static String getLogPath() {
        return staticLogPath;
    }
}