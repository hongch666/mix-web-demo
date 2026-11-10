package constants

// ===== 参数校验类 — 校验错误消息 =====

const (
	// 通用参数错误提示
	PARAM_ERR = "参数错误"
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
	VALIDATOR_SEARCH_MODE_MESSAGE = "搜索模式参数无效，仅支持 keyword/hybrid"
	// notbefore 标签的中文消息
	VALIDATOR_NOT_BEFORE_MESSAGE = "开始时间不能晚于结束时间"
)
