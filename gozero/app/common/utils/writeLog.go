package utils

import (
	"fmt"
	"os"
	"path/filepath"
	"time"

	"github.com/zeromicro/go-zero/core/logx"
)

// writeLog 直接写入日志到文件
func WriteLog(message string, level string) {
	// 使用默认路径
	logPath := filepath.Join("logs")

	// 如果日志路径不是绝对路径，则转换为绝对路径
	if !filepath.IsAbs(logPath) {
		// 获取当前工作目录
		wd, err := os.Getwd()
		if err != nil {
			logx.Error(GET_WORKING_DIR_ERROR)
		}
		// 拼接成绝对路径
		logPath = filepath.Join(wd, logPath)
	}

	// 确保日志目录存在
	if err := os.MkdirAll(logPath, 0o755); err != nil {
		logx.Error(CREATE_LOG_DIR_ERROR)
	}

	// 日志文件名 (按日期)
	today := time.Now().Format("2006-01-02")
	logFile := filepath.Join(logPath, fmt.Sprintf("app_%s.log", today))

	// 格式化日志消息
	timestamp := time.Now().Format("2006-01-02 15:04:05")
	logEntry := fmt.Sprintf("%s - %s - %s\n", timestamp, level, message)

	// 写入文件
	file, err := os.OpenFile(logFile, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0o666)
	if err != nil {
		logx.Error(OPEN_LOG_FILE_ERROR)
	}
	defer file.Close()

	if _, err := file.WriteString(logEntry); err != nil {
		logx.Error(WRITE_LOG_FILE_ERROR)
	}
}

// 便捷函数
func LogInfo(message string) {
	logx.Info(message)
	WriteLog(message, "INFO")
}

func LogError(message string) {
	logx.Error(message)
	WriteLog(message, "ERROR")
}

func LogWarning(message string) {
	logx.Info(message)
	WriteLog(message, "WARNING")
}

func LogDebug(message string) {
	logx.Debug(message)
	WriteLog(message, "DEBUG")
}

// SimpleLogger 结构体
type SimpleLogger struct{}

func (l *SimpleLogger) Info(message string) {
	LogInfo(message)
}

func (l *SimpleLogger) Error(message string) {
	LogError(message)
}

func (l *SimpleLogger) Warning(message string) {
	LogWarning(message)
}

func (l *SimpleLogger) Debug(message string) {
	LogDebug(message)
}

// 创建全局logger实例
var Log = &SimpleLogger{}
