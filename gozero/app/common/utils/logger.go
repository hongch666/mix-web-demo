package utils

import (
	"bufio"
	"context"
	"fmt"
	"os"
	"path/filepath"
	"sync"
	"time"

	"app/common/constants"

	"github.com/zeromicro/go-zero/core/logx"
)

// ZeroLogger 基于 go-zero logx 的日志工具，支持文件记录
type ZeroLogger struct {
	logPath     string
	ctx         context.Context
	fileMu      sync.Mutex // 保护文件句柄的并发访问
	currentFile *os.File   // 当前打开的日志文件句柄
	currentDate string     // 当前日志文件对应的日期，用于按天切换
}

// NewZeroLogger 创建新的日志实例
// logPath: 日志文件存放目录，例如 "./logs/gozero"
func NewZeroLogger(logPath string) (*ZeroLogger, error) {
	// 如果日志路径不是绝对路径，则转换为绝对路径
	if !filepath.IsAbs(logPath) {
		wd, err := os.Getwd()
		if err != nil {
			return nil, fmt.Errorf(constants.LOGGER_GET_WORKDIR_ERROR, err)
		}
		logPath = filepath.Join(wd, logPath)
	}

	// 确保日志目录存在
	if err := os.MkdirAll(logPath, 0o755); err != nil {
		return nil, fmt.Errorf(constants.LOGGER_CREATE_DIR_ERROR, err)
	}

	logger := &ZeroLogger{
		logPath: logPath,
		ctx:     context.Background(),
	}

	return logger, nil
}

// WithContext 返回一个包含上下文的新日志实例（共享同一日志文件路径）
func (z *ZeroLogger) WithContext(ctx context.Context) *ZeroLogger {
	if ctx == nil {
		return z
	}
	return &ZeroLogger{
		logPath: z.logPath,
		ctx:     ctx,
	}
}

// writeToFile 写入日志到文件（复用文件句柄，按天切换，使用缓冲写入提升性能）
func (z *ZeroLogger) writeToFile(message string, level string) {
	today := time.Now().Format("2006-01-02")
	logFile := filepath.Join(z.logPath, fmt.Sprintf("app_%s.log", today))

	// 格式化日志消息
	timestamp := time.Now().Format("2006-01-02 15:04:05")
	logEntry := fmt.Sprintf("%s - %s - %s\n", timestamp, level, message)

	z.fileMu.Lock()
	defer z.fileMu.Unlock()

	// 日期变化或文件未打开时，切换到新文件
	if z.currentFile == nil || z.currentDate != today {
		if z.currentFile != nil {
			z.currentFile.Close()
		}
		file, err := os.OpenFile(logFile, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0o666)
		if err != nil {
			logx.Error(fmt.Sprintf(constants.LOGGER_OPEN_FILE_ERROR, err))
			return
		}
		z.currentFile = file
		z.currentDate = today
	}

	// 使用缓冲写入减少系统调用
	writer := bufio.NewWriter(z.currentFile)
	if _, err := writer.WriteString(logEntry); err != nil {
		logx.Error(fmt.Sprintf(constants.LOGGER_WRITE_FILE_ERROR, err))
	}
	writer.Flush()
}

// Info 记录信息级别日志
func (z *ZeroLogger) Info(msg string) {
	logx.WithContext(z.ctx).Info(msg)
	z.writeToFile(msg, "INFO")
}

// Infof 记录格式化信息级别日志
func (z *ZeroLogger) Infof(format string, args ...interface{}) {
	msg := fmt.Sprintf(format, args...)
	logx.WithContext(z.ctx).Info(msg)
	z.writeToFile(msg, "INFO")
}

// Error 记录错误级别日志
func (z *ZeroLogger) Error(msg string) {
	logx.WithContext(z.ctx).Error(msg)
	z.writeToFile(msg, "ERROR")
}

// Errorf 记录格式化错误级别日志
func (z *ZeroLogger) Errorf(format string, args ...interface{}) {
	msg := fmt.Sprintf(format, args...)
	logx.WithContext(z.ctx).Error(msg)
	z.writeToFile(msg, "ERROR")
}

// Warning 记录警告级别日志
func (z *ZeroLogger) Warning(msg string) {
	logx.WithContext(z.ctx).Slow("[WARN] " + msg)
	z.writeToFile(msg, "WARN")
}

// Warningf 记录格式化警告级别日志
func (z *ZeroLogger) Warningf(format string, args ...interface{}) {
	msg := fmt.Sprintf(format, args...)
	logx.WithContext(z.ctx).Slow("[WARN] " + msg)
	z.writeToFile(msg, "WARN")
}

// Debug 记录调试级别日志
func (z *ZeroLogger) Debug(msg string) {
	logx.WithContext(z.ctx).Debug(msg)
	z.writeToFile(msg, "DEBUG")
}

// Debugf 记录格式化调试级别日志
func (z *ZeroLogger) Debugf(format string, args ...interface{}) {
	msg := fmt.Sprintf(format, args...)
	logx.WithContext(z.ctx).Debug(msg)
	z.writeToFile(msg, "DEBUG")
}
