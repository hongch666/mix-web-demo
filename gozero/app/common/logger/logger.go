package logger

import (
	"fmt"
	"os"
	"path/filepath"
	"time"

	"github.com/zeromicro/go-zero/core/logx"
)

// ZeroLogger 基于 go-zero logx 的日志工具，支持文件记录
type ZeroLogger struct {
	logPath string
}

// NewZeroLogger 创建新的日志实例
// logPath: 日志文件存放目录，例如 "./logs/gozero"
func NewZeroLogger(logPath string) (*ZeroLogger, error) {
	// 如果日志路径不是绝对路径，则转换为绝对路径
	if !filepath.IsAbs(logPath) {
		wd, err := os.Getwd()
		if err != nil {
			return nil, fmt.Errorf("获取工作目录失败: %w", err)
		}
		logPath = filepath.Join(wd, logPath)
	}

	// 确保日志目录存在
	if err := os.MkdirAll(logPath, 0755); err != nil {
		return nil, fmt.Errorf("创建日志目录失败: %w", err)
	}

	logger := &ZeroLogger{
		logPath: logPath,
	}

	return logger, nil
}

// writeToFile 写入日志到文件
func (z *ZeroLogger) writeToFile(message string, level string) {
	// 日志文件名 (按日期)
	today := time.Now().Format("2006-01-02")
	logFile := filepath.Join(z.logPath, fmt.Sprintf("app_%s.log", today))

	// 格式化日志消息
	timestamp := time.Now().Format("2006-01-02 15:04:05")
	logEntry := fmt.Sprintf("%s - %s - %s\n", timestamp, level, message)

	// 写入文件
	file, err := os.OpenFile(logFile, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0666)
	if err != nil {
		logx.Error(fmt.Sprintf("打开日志文件失败: %v", err))
		return
	}
	defer file.Close()

	if _, err := file.WriteString(logEntry); err != nil {
		logx.Error(fmt.Sprintf("写入日志文件失败: %v", err))
	}
}

// Info 记录信息级别日志
func (z *ZeroLogger) Info(msg string) {
	logx.Info(msg)
	z.writeToFile(msg, "INFO")
}

// Error 记录错误级别日志
func (z *ZeroLogger) Error(msg string) {
	logx.Error(msg)
	z.writeToFile(msg, "ERROR")
}

// Warning 记录警告级别日志
func (z *ZeroLogger) Warning(msg string) {
	logx.Info("[WARN] " + msg)
	z.writeToFile(msg, "WARN")
}

// Debug 记录调试级别日志
func (z *ZeroLogger) Debug(msg string) {
	logx.Debug(msg)
	z.writeToFile(msg, "DEBUG")
}
