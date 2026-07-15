package constants

// 参数校验类 — 校验错误消息
const (
	PARAM_ERR           = "参数错误"
	USER_ID_ERR         = "用户ID格式错误"
	FIELD_EMPTY_ERROR   = "%s不能为空"
	FIELD_POSITIVE_INT_ERROR = "%s必须是正整数"
	FIELD_GREATER_THAN_ZERO_ERROR = "%s必须大于0"

	CHAT_SENDER_ID_FIELD   = "发送者ID"
	CHAT_RECEIVER_ID_FIELD = "接收者ID"
	USER_ID_FIELD          = "用户ID"
	OTHER_USER_ID_FIELD    = "对方用户ID"

	CHAT_CONTENT_EMPTY_ERROR        = "消息内容不能为空"
	SEARCH_PAGE_GREATER_THAN_ZERO_ERROR     = "页码必须大于0"
	SEARCH_SIZE_GREATER_THAN_ZERO_ERROR     = "每页数量必须大于0"
	CHAT_HISTORY_PAGE_GREATER_THAN_ZERO_ERROR = "页码必须大于0"
	CHAT_HISTORY_SIZE_GREATER_THAN_ZERO_ERROR = "每页数量必须大于0"

	SEARCH_START_AFTER_END_ERROR = "开始时间不能晚于结束时间"
	SEARCH_TIME_FORMAT_ERROR     = "%s格式必须为%s"
	SEARCH_MODE_INVALID_ERROR    = "搜索模式参数无效，仅支持 keyword/hybrid/graph"
)
