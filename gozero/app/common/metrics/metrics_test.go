package metrics

import (
	"slices"
	"sort"
	"strings"
	"sync"
	"testing"

	"github.com/prometheus/client_golang/prometheus"
)

// sampleInfo 描述已注册指标在采集结果中的类型与首个采样的标签键值对
type sampleInfo struct {
	kind   string
	labels []string
}

// 默认注册表只允许注册一次, 重复调用 Init 会 panic, 包内测试用 once 保证只初始化一次
var initOnce sync.Once

// initMetrics 只初始化一次默认注册表, 避免同一进程内重复注册导致 panic
func initMetrics(t *testing.T) {
	t.Helper()
	initOnce.Do(Init)
}

// touchMetrics 按生产代码实际使用的标签顺序各写入一次采样, 取值互不相同以便校验位置对应关系
func touchMetrics() {
	ClientRequests.WithLabelValues("spring", "GET", "success").Inc()
	ClientDuration.WithLabelValues("spring", "GET").Observe(0.01)
	TaskRuns.WithLabelValues("es-sync", "success").Inc()
	TaskDuration.WithLabelValues("es-sync").Observe(0.01)
	SearchRequests.WithLabelValues("keyword", "success").Inc()
	SearchDuration.WithLabelValues("keyword").Observe(0.01)
}

// gatherSamples 采集默认注册表, 返回按指标名索引的类型与标签键值对, 标签按名称字母序排列
func gatherSamples(t *testing.T) map[string]sampleInfo {
	t.Helper()

	families, err := prometheus.DefaultGatherer.Gather()
	if err != nil {
		t.Fatalf("采集默认注册表失败: %v", err)
	}

	samples := make(map[string]sampleInfo, len(families))
	for _, family := range families {
		metricsOfFamily := family.GetMetric()
		if len(metricsOfFamily) == 0 {
			continue
		}
		labels := make([]string, 0, len(metricsOfFamily[0].GetLabel()))
		for _, label := range metricsOfFamily[0].GetLabel() {
			labels = append(labels, label.GetName()+"="+label.GetValue())
		}
		sort.Strings(labels)
		samples[family.GetName()] = sampleInfo{
			kind:   family.GetType().String(),
			labels: labels,
		}
	}
	return samples
}

// 验证 Init 把声明的指标全部注册到默认注册表且类型正确
func TestInitRegistersAllDeclaredMetrics(t *testing.T) {
	initMetrics(t)
	touchMetrics()
	samples := gatherSamples(t)

	cases := []struct {
		name     string
		wantKind string
	}{
		{NameClientRequests, "COUNTER"},
		{NameClientDuration, "HISTOGRAM"},
		{NameTaskRuns, "COUNTER"},
		{NameTaskDuration, "HISTOGRAM"},
		{NameSearchRequests, "COUNTER"},
		{NameSearchDuration, "HISTOGRAM"},
	}

	for _, testCase := range cases {
		sample, ok := samples[testCase.name]
		if !ok {
			t.Fatalf("指标 %s 未注册到默认注册表", testCase.name)
		}
		if sample.kind != testCase.wantKind {
			t.Fatalf("指标 %s 类型 = %s, 期望 %s", testCase.name, sample.kind, testCase.wantKind)
		}
	}

	// 默认注册表还包含 go_/process_ 等运行时指标, 只统计本包声明的 mix_ 前缀指标
	registered := 0
	for name := range samples {
		if strings.HasPrefix(name, "mix_") {
			registered++
		}
	}
	if registered != len(cases) {
		t.Fatalf("已注册的 mix_ 指标数量 = %d, 期望 %d, 新增指标需同步加入 Init", registered, len(cases))
	}
}

// 验证标签名与生产调用点的取值位置一一对应, 只比较标签名会漏掉顺序错位的隐性问题
func TestMetricsExposeProductionLabelValues(t *testing.T) {
	initMetrics(t)
	touchMetrics()
	samples := gatherSamples(t)

	cases := []struct {
		name       string
		wantLabels []string
	}{
		{
			NameClientRequests,
			[]string{LabelMethod + "=GET", LabelOutcome + "=success", LabelTargetService + "=spring"},
		},
		{
			NameClientDuration,
			[]string{LabelMethod + "=GET", LabelTargetService + "=spring"},
		},
		{
			NameTaskRuns,
			[]string{LabelResult + "=success", LabelTask + "=es-sync"},
		},
		{
			NameTaskDuration,
			[]string{LabelTask + "=es-sync"},
		},
		{
			NameSearchRequests,
			[]string{LabelMode + "=keyword", LabelResult + "=success"},
		},
		{
			NameSearchDuration,
			[]string{LabelMode + "=keyword"},
		},
	}

	for _, testCase := range cases {
		sample, ok := samples[testCase.name]
		if !ok {
			t.Fatalf("指标 %s 未注册到默认注册表", testCase.name)
		}
		if !slices.Equal(sample.labels, testCase.wantLabels) {
			t.Fatalf(
				"指标 %s 标签 = %s, 期望 %s",
				testCase.name,
				strings.Join(sample.labels, ","),
				strings.Join(testCase.wantLabels, ","),
			)
		}
	}
}
