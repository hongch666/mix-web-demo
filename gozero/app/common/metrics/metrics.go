package metrics

import (
	"app/common/constants"

	"github.com/prometheus/client_golang/prometheus"
)

var (
	ClientRequests = prometheus.NewCounterVec(prometheus.CounterOpts{
		Name: NameClientRequests,
		Help: constants.METRIC_HELP_CLIENT_REQUESTS,
	}, []string{LabelTargetService, LabelMethod, LabelOutcome})
	ClientDuration = prometheus.NewHistogramVec(prometheus.HistogramOpts{
		Name:    NameClientDuration,
		Help:    constants.METRIC_HELP_CLIENT_DURATION,
		Buckets: prometheus.DefBuckets,
	}, []string{LabelTargetService, LabelMethod})
	TaskRuns = prometheus.NewCounterVec(prometheus.CounterOpts{
		Name: NameTaskRuns,
		Help: constants.METRIC_HELP_TASK_RUNS,
	}, []string{LabelTask, LabelResult})
	TaskDuration = prometheus.NewHistogramVec(prometheus.HistogramOpts{
		Name:    NameTaskDuration,
		Help:    constants.METRIC_HELP_TASK_DURATION,
		Buckets: prometheus.DefBuckets,
	}, []string{LabelTask})
	SearchRequests = prometheus.NewCounterVec(prometheus.CounterOpts{
		Name: NameSearchRequests,
		Help: constants.METRIC_HELP_SEARCH_REQUESTS,
	}, []string{LabelMode, LabelResult})
	SearchDuration = prometheus.NewHistogramVec(prometheus.HistogramOpts{
		Name:    NameSearchDuration,
		Help:    constants.METRIC_HELP_SEARCH_DURATION,
		Buckets: prometheus.DefBuckets,
	}, []string{LabelMode})
)

// Init 将客户端调用、定时任务与搜索等全部 Prometheus 指标注册到默认注册表
func Init() {
	prometheus.MustRegister(ClientRequests, ClientDuration, TaskRuns, TaskDuration, SearchRequests, SearchDuration)
}
