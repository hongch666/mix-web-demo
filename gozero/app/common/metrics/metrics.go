package metrics

import "github.com/prometheus/client_golang/prometheus"

var (
	ClientRequests = prometheus.NewCounterVec(prometheus.CounterOpts{
		Name: NameClientRequests,
		Help: "下游服务调用次数",
	}, []string{LabelTargetService, LabelMethod, LabelOutcome})
	ClientDuration = prometheus.NewHistogramVec(prometheus.HistogramOpts{
		Name:    NameClientDuration,
		Help:    "下游服务调用耗时",
		Buckets: prometheus.DefBuckets,
	}, []string{LabelTargetService, LabelMethod})
	TaskRuns = prometheus.NewCounterVec(prometheus.CounterOpts{
		Name: NameTaskRuns,
		Help: "定时任务执行次数",
	}, []string{LabelTask, LabelResult})
	TaskDuration = prometheus.NewHistogramVec(prometheus.HistogramOpts{
		Name:    NameTaskDuration,
		Help:    "定时任务执行耗时",
		Buckets: prometheus.DefBuckets,
	}, []string{LabelTask})
	SearchRequests = prometheus.NewCounterVec(prometheus.CounterOpts{
		Name: NameSearchRequests,
		Help: "搜索请求次数",
	}, []string{LabelMode, LabelResult})
	SearchDuration = prometheus.NewHistogramVec(prometheus.HistogramOpts{
		Name:    NameSearchDuration,
		Help:    "搜索请求耗时",
		Buckets: prometheus.DefBuckets,
	}, []string{LabelMode})
)

func Init() {
	prometheus.MustRegister(ClientRequests, ClientDuration, TaskRuns, TaskDuration, SearchRequests, SearchDuration)
}
