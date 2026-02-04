package config

import (
	"runtime"
	"time"

	"github.com/hongch666/mix-web-demo/gin/common/goroutine"
)

// InitGoroutineMonitor 初始化goroutine监控
func InitGoroutineMonitor() {
	monitor := goroutine.GetMonitor()
	monitor.SetInterval(5 * time.Second) // 设置采样间隔为5秒
	monitor.Start()

	// 注册程序退出时的清理函数
	runtime.SetFinalizer(monitor, func(m *goroutine.GoroutineMonitor) {
		m.Stop()
	})
}
