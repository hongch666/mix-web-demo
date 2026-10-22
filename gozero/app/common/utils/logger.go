package utils

import (
	"bufio"
	"context"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"time"

	"app/common/constants"

	"github.com/zeromicro/go-zero/core/logx"
	zerotrace "github.com/zeromicro/go-zero/core/trace"
)

// logFileHolder 共享的文件句柄，供同一路径下的派生日志实例复用
// 派生实例各自持有句柄会在高频请求下不断新建文件描述符，只有等 GC 回收才关闭
type logFileHolder struct {
	mu          sync.Mutex // 保护文件句柄的并发访问
	file        *os.File   // 当前打开的日志文件句柄
	currentDate string     // 当前日志文件对应的日期，用于按天切换
}

// ZeroLogger 基于 go-zero logx 的日志工具，支持文件记录
type ZeroLogger struct {
	logPath string
	ctx     context.Context
	holder  *logFileHolder
	// 是否在日志行写入时间戳，容器部署关闭后由 Loki 采集时间承担
	includeTimestamp bool
}

// NewZeroLogger 创建新的日志实例
// logPath: 日志文件存放目录，必须由配置显式提供，例如 "../../logs/gozero"
// includeTimestamp: 可选开关，缺省写入时间戳
func NewZeroLogger(logPath string, includeTimestamp ...bool) (*ZeroLogger, error) {
	// 路径缺失时直接报错，不再回退到进程工作目录，避免日志写到意外的位置
	if strings.TrimSpace(logPath) == "" {
		return nil, errors.New(constants.LOGGER_PATH_EMPTY_ERROR)
	}

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

	enabled := true
	if len(includeTimestamp) > 0 {
		enabled = includeTimestamp[0]
	}

	logger := &ZeroLogger{
		logPath:          logPath,
		ctx:              context.Background(),
		holder:           &logFileHolder{},
		includeTimestamp: enabled,
	}

	return logger, nil
}

// WithContext 返回一个包含上下文的新日志实例（共享同一日志文件与文件句柄）
func (z *ZeroLogger) WithContext(ctx context.Context) *ZeroLogger {
	if ctx == nil {
		return z
	}
	if z.holder == nil {
		z.holder = &logFileHolder{}
	}
	return &ZeroLogger{
		logPath:          z.logPath,
		ctx:              ctx,
		holder:           z.holder,
		includeTimestamp: z.includeTimestamp,
	}
}

// writeToFile 写入日志到文件（复用文件句柄，按天切换，使用缓冲写入提升性能）
func (z *ZeroLogger) writeToFile(message string, level string) {
	today := time.Now().Format("2006-01-02")
	logFile := filepath.Join(z.logPath, fmt.Sprintf("app_%s.log", today))

	// 格式化日志消息
	timestamp := time.Now().Format(constants.DateTimeFormat)
	traceID := zerotrace.TraceIDFromContext(z.ctx)
	if traceID == "" {
		traceID = constants.EmptyTraceID
	}
	var logEntry string
	if z.includeTimestamp {
		logEntry = fmt.Sprintf(constants.TraceLogFormat, timestamp, level, traceID, message)
	} else {
		logEntry = fmt.Sprintf(constants.TraceLogFormatNoTime, level, traceID, message)
	}

	z.holder.mu.Lock()
	defer z.holder.mu.Unlock()

	// 日期变化或文件未打开时，切换到新文件
	if z.holder.file == nil || z.holder.currentDate != today {
		if z.holder.file != nil {
			z.holder.file.Close()
		}
		file, err := os.OpenFile(logFile, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0o666)
		if err != nil {
			logx.Error(fmt.Sprintf(constants.LOGGER_OPEN_FILE_ERROR, err))
			return
		}
		z.holder.file = file
		z.holder.currentDate = today
	}

	// 使用缓冲写入减少系统调用
	writer := bufio.NewWriter(z.holder.file)
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

// Close 关闭日志文件句柄，刷新缓冲区
// 派生实例与根实例共享同一句柄，重复关闭是安全的
func (z *ZeroLogger) Close() error {
	if z.holder == nil {
		return nil
	}

	z.holder.mu.Lock()
	defer z.holder.mu.Unlock()

	if z.holder.file != nil {
		err := z.holder.file.Close()
		z.holder.file = nil
		z.holder.currentDate = ""
		return err
	}
	return nil
}
