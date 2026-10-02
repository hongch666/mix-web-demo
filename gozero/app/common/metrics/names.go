package metrics

const (
	NameClientRequests = "mix_client_requests_total"
	NameClientDuration = "mix_client_request_duration_seconds"
	NameTaskRuns       = "mix_task_runs_total"
	NameTaskDuration   = "mix_task_duration_seconds"
	NameSearchRequests = "mix_search_requests_total"
	NameSearchDuration = "mix_search_duration_seconds"

	LabelTargetService = "target_service"
	LabelMethod        = "method"
	LabelOutcome       = "outcome"
	LabelTask          = "task"
	LabelResult        = "result"
	LabelMode          = "mode"
)
