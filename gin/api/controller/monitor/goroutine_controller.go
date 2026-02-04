package monitor

import (
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/hongch666/mix-web-demo/gin/common/goroutine"
	"github.com/hongch666/mix-web-demo/gin/common/utils"
)

// @Summary 获取goroutine统计信息
// @Description 获取当前goroutine的统计信息，包括当前数量、峰值、最小值、平均值、监控时长等（使用pprof）
// @Tags 监控
// @Accept json
// @Produce json
// @Success 200 {object} map[string]interface{} "包含 current、peak、min、average、duration 等字段"
// @Failure 500 {object} map[string]interface{} "服务器内部错误"
// @Router /monitor/goroutine/stats [get]
func GetGoroutineStats(c *gin.Context) {
	monitor := goroutine.GetMonitor()
	stats := monitor.GetStats()
	utils.RespondSuccess(c, stats)
}

// @Summary 获取goroutine历史数据
// @Description 获取所有采样的goroutine历史数据，包括时间戳、数量和pprof详细堆栈信息
// @Tags 监控
// @Accept json
// @Produce json
// @Success 200 {object} map[string]interface{} "包含 Timestamp、Count 和 Details 的历史数据列表"
// @Failure 500 {object} map[string]interface{} "服务器内部错误"
// @Router /monitor/goroutine/history [get]
func GetGoroutineHistory(c *gin.Context) {
	monitor := goroutine.GetMonitor()
	history := monitor.GetHistory()
	utils.RespondSuccess(c, history)
}

// @Summary 获取峰值时刻的详细goroutine信息
// @Description 获取峰值时刻对应的pprof profile详细堆栈信息
// @Tags 监控
// @Accept json
// @Produce json
// @Success 200 {object} map[string]interface{} "包含 timestamp、count 和 details(pprof堆栈)"
// @Failure 500 {object} map[string]interface{} "服务器内部错误"
// @Router /monitor/goroutine/peak-details [get]
func GetPeakDetails(c *gin.Context) {
	monitor := goroutine.GetMonitor()
	details := monitor.GetPeakDetails()
	utils.RespondSuccess(c, details)
}

// @Summary 获取当前pprof goroutine profile
// @Description 获取当前实时的pprof goroutine profile信息
// @Tags 监控
// @Accept json
// @Produce json
// @Success 200 {object} map[string]interface{} "pprof profile数据"
// @Failure 500 {object} map[string]interface{} "服务器内部错误"
// @Router /monitor/goroutine/current-profile [get]
func GetCurrentProfile(c *gin.Context) {
	monitor := goroutine.GetMonitor()
	profile := monitor.GetCurrentPprofProfile()
	c.String(http.StatusOK, profile)
}

// @Summary 按类型统计goroutine
// @Description 统计当前goroutine的类型分布
// @Tags 监控
// @Accept json
// @Produce json
// @Success 200 {object} map[string]interface{} "按类型统计的goroutine数量"
// @Failure 500 {object} map[string]interface{} "服务器内部错误"
// @Router /monitor/goroutine/by-type [get]
func GetGoroutinesByType(c *gin.Context) {
	monitor := goroutine.GetMonitor()
	typeStats := monitor.GetGoroutinesByType()
	utils.RespondSuccess(c, typeStats)
}

// @Summary 重置goroutine监控数据
// @Description 重置所有监控数据，开始新一轮的监控统计
// @Tags 监控
// @Accept json
// @Produce json
// @Success 200 {object} map[string]interface{} "重置成功提示信息"
// @Failure 500 {object} map[string]interface{} "服务器内部错误"
// @Router /monitor/goroutine/reset [post]
func ResetGoroutineMonitor(c *gin.Context) {
	monitor := goroutine.GetMonitor()
	monitor.Reset()
	utils.RespondSuccess(c, "监控数据已重置")
}
