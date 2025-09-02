package utils

import (
	"fmt"
	"gin_proj/config"
	"log"
	"os"
	"path/filepath"
	"time"
)

// writeLog 直接写入日志到文件
func WriteLog(message string, level string) {
	// 获取日志路径配置
	logPath := config.Config.Logs.Path

	if logPath == "" {
		// 如果没有配置日志路径，使用默认路径
		logPath = filepath.Join("logs")
	}
	// 如果日志路径不是绝对路径，则转换为绝对路径
	if !filepath.IsAbs(logPath) {
		// 获取当前工作目录
		wd, err := os.Getwd()
		if err != nil {
			panic(fmt.Errorf("获取当前工作目录失败: %s", err))
		}
		// 拼接成绝对路径
		logPath = filepath.Join(wd, logPath)
	}

	// 确保日志目录存在
	if err := os.MkdirAll(logPath, 0755); err != nil {
		panic(fmt.Errorf("创建日志目录失败: %s", err))
	}

	// 日志文件名 (按日期)
	today := time.Now().Format("2006-01-02")
	logFile := filepath.Join(logPath, fmt.Sprintf("app_%s.log", today))

	// 格式化日志消息
	timestamp := time.Now().Format("2006-01-02 15:04:05")
	logEntry := fmt.Sprintf("%s - %s - %s\n", timestamp, level, message)

	// 写入文件
	file, err := os.OpenFile(logFile, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0666)
	if err != nil {
		panic(fmt.Errorf("打开日志文件失败: %s", err))
	}
	defer file.Close()

	if _, err := file.WriteString(logEntry); err != nil {
		panic(fmt.Errorf("写入日志文件失败: %s", err))
	}
}

// 便捷函数
func LogInfo(message string) {
	log.Println(message)
	WriteLog(message, "INFO")
}

func LogError(message string) {
	log.Println(message)
	WriteLog(message, "ERROR")
}

func LogWarning(message string) {
	log.Println(message)
	WriteLog(message, "WARNING")
}

func LogDebug(message string) {
	log.Println(message)
	WriteLog(message, "DEBUG")
}

// SimpleLogger 结构体，模仿Python的类
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
var FileLogger = &SimpleLogger{}
