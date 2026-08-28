package com.hcsy.spring.common.utils;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.OutputStreamWriter;
import java.nio.charset.StandardCharsets;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import com.hcsy.spring.common.constants.Messages;

import jakarta.annotation.PostConstruct;
import lombok.extern.slf4j.Slf4j;

/**
 * 简单日志记录器
 * 同时输出到 SLF4J 与按日期滚动的日志文件
 */
@Slf4j
@Component
public class SimpleLogger {

    private static final DateTimeFormatter DATE_FORMATTER = DateTimeFormatter.ofPattern("yyyy-MM-dd");
    private static final DateTimeFormatter TIMESTAMP_FORMATTER = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

    @Value("${logging.file.path}")
    private String logPath;

    /**
     * 初始化日志目录
     */
    @PostConstruct
    public void init() {
        File logDir = new File(logPath);
        if (!logDir.exists()) {
            logDir.mkdirs();
        }
        log.info(Messages.LOG_INIT, logPath);
    }

    public void info(String message) {
        log.info(message);
        writeLog(message, "INFO");
    }

    public void error(String message) {
        log.error(message);
        writeLog(message, "ERROR");
    }

    public void warning(String message) {
        log.warn(message);
        writeLog(message, "WARNING");
    }

    public void debug(String message) {
        log.debug(message);
        writeLog(message, "DEBUG");
    }

    // 支持格式化字符串
    public void info(String format, Object... args) {
        info(String.format(format, args));
    }

    public void error(String format, Object... args) {
        error(String.format(format, args));
    }

    public void warning(String format, Object... args) {
        warning(String.format(format, args));
    }

    public void debug(String format, Object... args) {
        debug(String.format(format, args));
    }

    /**
     * 直接写入日志到文件
     */
    private void writeLog(String message, String level) {
        try {
            // 确保日志目录存在
            File logDir = new File(logPath);
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

            // 写入文件，指定UTF-8编码
            try (OutputStreamWriter writer = new OutputStreamWriter(
                new FileOutputStream(logFile, true), StandardCharsets.UTF_8)) {
                writer.write(logEntry);
                writer.flush();
            }

        } catch (IOException e) {
            log.error(Messages.LOG_WRITE, e.getMessage(), e);
        }
    }
}
