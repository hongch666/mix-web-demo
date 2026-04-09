package utils

import (
	"fmt"
	"runtime/debug"
)

type panicLogger interface {
	Error(msg string)
}

// SafeGo 在独立 goroutine 中执行任务，并在 panic 时记录错误和堆栈，避免子 goroutine 直接打崩进程
func SafeGo(log panicLogger, taskName string, fn func()) {
	go func() {
		defer func() {
			if err := recover(); err != nil {
				message := fmt.Sprintf(SAFE_GO_PANIC_RECOVERED_MESSAGE, taskName, err, debug.Stack())
				if log != nil {
					log.Error(message)
				}
			}
		}()

		fn()
	}()
}
