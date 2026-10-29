package constants

// ===== 参数校验类 — 校验错误消息 =====

const (
	// ===== 请求参数校验 =====

	// 通用参数错误提示
	PARAM_ERR = "参数错误"
	// 字段为空的校验消息模板
	FIELD_EMPTY_ERROR = "%s不能为空"
	// 字段必须是正整数的校验消息模板
	FIELD_POSITIVE_INT_ERROR = "%s必须是正整数"
	// 字段必须大于 0 的校验消息模板
	FIELD_GREATER_THAN_ZERO_ERROR = "%s必须大于0"

	// ===== 校验字段名 =====

	// 聊天发送者字段的中文名
	CHAT_SENDER_ID_FIELD = "发送者ID"
	// 聊天接收者字段的中文名
	CHAT_RECEIVER_ID_FIELD = "接收者ID"
	// 用户 ID 字段的中文名
	USER_ID_FIELD = "用户ID"
	// 对方用户 ID 字段的中文名
	OTHER_USER_ID_FIELD = "对方用户ID"

	// ===== 业务校验消息 =====

	// 聊天内容为空的校验消息
	CHAT_CONTENT_EMPTY_ERROR = "消息内容不能为空"
	// 搜索页码必须大于 0 的校验消息
	SEARCH_PAGE_GREATER_THAN_ZERO_ERROR = "页码必须大于0"
	// 搜索每页数量必须大于 0 的校验消息
	SEARCH_SIZE_GREATER_THAN_ZERO_ERROR = "每页数量必须大于0"
	// 聊天历史页码必须大于 0 的校验消息
	CHAT_HISTORY_PAGE_GREATER_THAN_ZERO_ERROR = SEARCH_PAGE_GREATER_THAN_ZERO_ERROR
	// 聊天历史每页数量必须大于 0 的校验消息
	CHAT_HISTORY_SIZE_GREATER_THAN_ZERO_ERROR = SEARCH_SIZE_GREATER_THAN_ZERO_ERROR

	// 开始时间晚于结束时间的校验消息
	SEARCH_START_AFTER_END_ERROR = "开始时间不能晚于结束时间"
	// 时间格式错误的校验消息模板
	SEARCH_TIME_FORMAT_ERROR = "%s格式必须为%s"
	// 搜索模式取值非法的校验消息
	SEARCH_MODE_INVALID_ERROR = "搜索模式参数无效，仅支持 keyword/hybrid/graph"
)

// ===== 参数校验器类 — validator 的消息使用 {0}/{1} 占位，与上面的 %s 风格区分 =====

const (
	// ===== 校验器消息 =====

	// 校验器翻译器初始化失败的日志消息
	VALIDATOR_TRANSLATOR_INIT_FAIL = "初始化校验器翻译器失败: %v"
	// 校验规则注册失败的日志消息
	VALIDATOR_RULE_REGISTER_FAIL = "注册校验规则 %s 失败: %v"
	// 参数校验器初始化失败的日志消息
	VALIDATOR_INIT_FAIL = "初始化参数校验器失败: %v"
	// notblank 标签的中文消息
	VALIDATOR_NOT_BLANK_MESSAGE = "{0}不能为空"
	// positiveint 标签的中文消息
	VALIDATOR_POSITIVE_INT_MESSAGE = "{0}必须是正整数"
	// datetime 标签的中文消息
	VALIDATOR_DATETIME_MESSAGE = "{0}格式必须为" + DateTimeFormat
	// maxrunes 标签的中文消息
	VALIDATOR_MAX_RUNES_MESSAGE = "{0}长度不能超过{1}个字符"
	// searchmode 标签的中文消息
	VALIDATOR_SEARCH_MODE_MESSAGE = "搜索模式参数无效，仅支持 keyword/hybrid/graph"
	// notbefore 标签的中文消息
	VALIDATOR_NOT_BEFORE_MESSAGE = "开始时间不能晚于结束时间"
)
