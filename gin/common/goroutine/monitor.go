package goroutine

import (
	"bytes"
	"fmt"
	"log"
	"runtime"
	"runtime/pprof"
	"strings"
	"sync"
	"time"
)

// GoroutineMonitor 用于监控goroutine的数量和峰值（基于pprof）
type GoroutineMonitor struct {
	peakCount     int
	minCount      int
	startTime     time.Time
	mutex         sync.RWMutex
	isMonitoring  bool
	stopChan      chan struct{}
	interval      time.Duration
	historyData   []GoroutineSnapshot
	maxHistoryLen int
	peakTime      time.Time
	minTime       time.Time
}

// GoroutineSnapshot 记录某个时刻的goroutine快照（包含详细信息）
type GoroutineSnapshot struct {
	Timestamp time.Time
	Count     int
	Details   string // goroutine的详细堆栈信息
}

var (
	monitor *GoroutineMonitor
	once    sync.Once
)

// GetMonitor 获取全局监控器单例
func GetMonitor() *GoroutineMonitor {
	once.Do(func() {
		currentCount := runtime.NumGoroutine()
		monitor = &GoroutineMonitor{
			startTime:     time.Now(),
			stopChan:      make(chan struct{}),
			interval:      5 * time.Second, // 默认5秒采样一次
			historyData:   make([]GoroutineSnapshot, 0, 1000),
			maxHistoryLen: 1000,
			peakCount:     currentCount,
			minCount:      currentCount,
			peakTime:      time.Now(),
			minTime:       time.Now(),
		}
	})
	return monitor
}

// Start 开始监控goroutine
func (gm *GoroutineMonitor) Start() {
	gm.mutex.Lock()
	defer gm.mutex.Unlock()

	if gm.isMonitoring {
		log.Println("[Goroutine Monitor] 监控已经在运行")
		return
	}

	gm.isMonitoring = true
	log.Printf("[Goroutine Monitor] 开始监控 (采样间隔: %v，使用pprof)", gm.interval)

	go gm.monitorLoop()
}

// Stop 停止监控
func (gm *GoroutineMonitor) Stop() {
	gm.mutex.Lock()
	defer gm.mutex.Unlock()

	if !gm.isMonitoring {
		return
	}

	gm.isMonitoring = false
	close(gm.stopChan)
	gm.PrintSummary()
}

// monitorLoop 监控循环
func (gm *GoroutineMonitor) monitorLoop() {
	ticker := time.NewTicker(gm.interval)
	defer ticker.Stop()

	for {
		select {
		case <-gm.stopChan:
			return
		case <-ticker.C:
			gm.collectSnapshot()
		}
	}
}

// collectSnapshot 使用pprof采集一个快照
func (gm *GoroutineMonitor) collectSnapshot() {
	count := runtime.NumGoroutine()
	details := gm.getPprofGoroutineInfo()

	gm.mutex.Lock()
	defer gm.mutex.Unlock()

	if count > gm.peakCount {
		gm.peakCount = count
		gm.peakTime = time.Now()
	}

	if count < gm.minCount {
		gm.minCount = count
		gm.minTime = time.Now()
	}

	// 记录历史数据
	snapshot := GoroutineSnapshot{
		Timestamp: time.Now(),
		Count:     count,
		Details:   details,
	}

	if len(gm.historyData) < gm.maxHistoryLen {
		gm.historyData = append(gm.historyData, snapshot)
	} else {
		// 保持固定大小，移除最早的数据
		gm.historyData = append(gm.historyData[1:], snapshot)
	}
}

// getPprofGoroutineInfo 使用pprof获取goroutine的详细信息
func (gm *GoroutineMonitor) getPprofGoroutineInfo() string {
	profile := pprof.Lookup("goroutine")
	if profile == nil {
		return "Unable to get goroutine profile"
	}

	var buf bytes.Buffer
	profile.WriteTo(&buf, 2) // debug=2 获取完整堆栈信息
	return buf.String()
}

// GetStats 获取统计信息
func (gm *GoroutineMonitor) GetStats() map[string]interface{} {
	gm.mutex.RLock()
	defer gm.mutex.RUnlock()

	duration := time.Since(gm.startTime)
	average := gm.calculateAverage()
	current := runtime.NumGoroutine()

	return map[string]interface{}{
		"current":        current,
		"peak":           gm.peakCount,
		"peakTime":       gm.peakTime.Format("2006-01-02 15:04:05"),
		"min":            gm.minCount,
		"minTime":        gm.minTime.Format("2006-01-02 15:04:05"),
		"average":        fmt.Sprintf("%.2f", average),
		"duration":       duration.String(),
		"durationSecond": int(duration.Seconds()),
		"startTime":      gm.startTime.Format("2006-01-02 15:04:05"),
		"lastUpdate":     time.Now().Format("2006-01-02 15:04:05"),
		"sampledCount":   len(gm.historyData),
		"monitorBackend": "pprof",
	}
}

// calculateAverage 计算平均值
func (gm *GoroutineMonitor) calculateAverage() float64 {
	if len(gm.historyData) == 0 {
		return 0
	}

	sum := 0
	for _, data := range gm.historyData {
		sum += data.Count
	}

	return float64(sum) / float64(len(gm.historyData))
}

// PrintSummary 打印统计摘要
func (gm *GoroutineMonitor) PrintSummary() {
	stats := gm.GetStats()
	log.Println("========== Goroutine 监控统计 (pprof) ==========")
	log.Printf("当前数量:     %d\n", stats["current"])
	log.Printf("峰值数量:     %d (时刻: %s)\n", stats["peak"], stats["peakTime"])
	log.Printf("最小数量:     %d (时刻: %s)\n", stats["min"], stats["minTime"])
	log.Printf("平均数量:     %s\n", stats["average"])
	log.Printf("监控时长:     %s\n", stats["duration"])
	log.Printf("采样次数:     %d\n", stats["sampledCount"])
	log.Printf("开始时间:     %s\n", stats["startTime"])
	log.Printf("监控后端:     %s\n", stats["monitorBackend"])
	log.Println("==============================================")
}

// GetHistory 获取历史数据
func (gm *GoroutineMonitor) GetHistory() []GoroutineSnapshot {
	gm.mutex.RLock()
	defer gm.mutex.RUnlock()

	// 返回副本
	result := make([]GoroutineSnapshot, len(gm.historyData))
	copy(result, gm.historyData)
	return result
}

// SetInterval 设置采样间隔
func (gm *GoroutineMonitor) SetInterval(interval time.Duration) {
	gm.mutex.Lock()
	defer gm.mutex.Unlock()

	gm.interval = interval
	log.Printf("[Goroutine Monitor] 采样间隔已更新为: %v", interval)
}

// Reset 重置监控数据
func (gm *GoroutineMonitor) Reset() {
	gm.mutex.Lock()
	defer gm.mutex.Unlock()

	currentCount := runtime.NumGoroutine()
	gm.peakCount = currentCount
	gm.minCount = currentCount
	gm.startTime = time.Now()
	gm.peakTime = time.Now()
	gm.minTime = time.Now()
	gm.historyData = gm.historyData[:0]
	log.Println("[Goroutine Monitor] 数据已重置")
}

// GetPeakDetails 获取峰值时刻的详细goroutine信息
func (gm *GoroutineMonitor) GetPeakDetails() map[string]interface{} {
	gm.mutex.RLock()
	defer gm.mutex.RUnlock()

	// 找到峰值对应的快照
	var peakSnapshot GoroutineSnapshot
	for _, snapshot := range gm.historyData {
		if snapshot.Count == gm.peakCount {
			peakSnapshot = snapshot
			break
		}
	}

	return map[string]interface{}{
		"timestamp": peakSnapshot.Timestamp.Format("2006-01-02 15:04:05"),
		"count":     gm.peakCount,
		"details":   peakSnapshot.Details,
	}
}

// GetCurrentPprofProfile 获取当前pprof goroutine profile
func (gm *GoroutineMonitor) GetCurrentPprofProfile() string {
	profile := pprof.Lookup("goroutine")
	if profile == nil {
		return "Unable to get goroutine profile"
	}

	var buf bytes.Buffer
	profile.WriteTo(&buf, 2) // debug=2 获取完整堆栈信息
	return buf.String()
}

// GetGoroutinesByType 按类型统计goroutine
func (gm *GoroutineMonitor) GetGoroutinesByType() map[string]int {
	profile := pprof.Lookup("goroutine")
	if profile == nil {
		return make(map[string]int)
	}

	var buf bytes.Buffer
	profile.WriteTo(&buf, 1)

	stats := make(map[string]int)
	lines := strings.Split(buf.String(), "\n")
	for _, line := range lines {
		if strings.HasPrefix(line, "goroutine") {
			// 提取goroutine类型信息
			parts := strings.Fields(line)
			if len(parts) > 0 {
				typeKey := "unknown"
				for _, part := range parts {
					if strings.HasPrefix(part, "[") {
						typeKey = strings.TrimPrefix(strings.TrimSuffix(part, "]"), "[")
						break
					}
				}
				stats[typeKey]++
			}
		}
	}

	return stats
}
