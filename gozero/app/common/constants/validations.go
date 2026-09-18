package constants

// 参数校验类 — 校验错误消息
const (
	PARAM_ERR                     = "参数错误"
	FIELD_EMPTY_ERROR             = "%s不能为空"
	FIELD_POSITIVE_INT_ERROR      = "%s必须是正整数"
	FIELD_GREATER_THAN_ZERO_ERROR = "%s必须大于0"

	CHAT_SENDER_ID_FIELD   = "发送者ID"
	CHAT_RECEIVER_ID_FIELD = "接收者ID"
	USER_ID_FIELD          = "用户ID"
	OTHER_USER_ID_FIELD    = "对方用户ID"

	CHAT_CONTENT_EMPTY_ERROR                  = "消息内容不能为空"
	SEARCH_PAGE_GREATER_THAN_ZERO_ERROR       = "页码必须大于0"
	SEARCH_SIZE_GREATER_THAN_ZERO_ERROR       = "每页数量必须大于0"
	CHAT_HISTORY_PAGE_GREATER_THAN_ZERO_ERROR = SEARCH_PAGE_GREATER_THAN_ZERO_ERROR
	CHAT_HISTORY_SIZE_GREATER_THAN_ZERO_ERROR = SEARCH_SIZE_GREATER_THAN_ZERO_ERROR

	SEARCH_START_AFTER_END_ERROR = "开始时间不能晚于结束时间"
	SEARCH_TIME_FORMAT_ERROR     = "%s格式必须为%s"
	SEARCH_MODE_INVALID_ERROR    = "搜索模式参数无效，仅支持 keyword/hybrid/graph"
)

// 参数校验器类 — validator 的消息使用 {0}/{1} 占位，与上面的 %s 风格区分
const (
	VALIDATOR_TRANSLATOR_INIT_FAIL = "初始化校验器翻译器失败: %v"
	VALIDATOR_RULE_REGISTER_FAIL   = "注册校验规则 %s 失败: %v"
	VALIDATOR_INIT_FAIL            = "初始化参数校验器失败: %v"
	VALIDATOR_NOT_BLANK_MESSAGE    = "{0}不能为空"
	VALIDATOR_POSITIVE_INT_MESSAGE = "{0}必须是正整数"
	VALIDATOR_DATETIME_MESSAGE     = "{0}格式必须为" + DateTimeFormat
	VALIDATOR_MAX_RUNES_MESSAGE    = "{0}长度不能超过{1}个字符"
	VALIDATOR_SEARCH_MODE_MESSAGE  = "搜索模式参数无效，仅支持 keyword/hybrid/graph"
	VALIDATOR_NOT_BEFORE_MESSAGE   = "开始时间不能晚于结束时间"
)
