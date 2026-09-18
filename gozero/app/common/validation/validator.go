package validation

import (
	"errors"
	"fmt"
	"net/http"
	"reflect"
	"strconv"
	"strings"
	"time"
	"unicode/utf8"

	"app/common/constants"
	"app/common/exceptions"

	"github.com/go-playground/locales/zh"
	ut "github.com/go-playground/universal-translator"
	"github.com/go-playground/validator/v10"
	zhtranslations "github.com/go-playground/validator/v10/translations/zh"
	"github.com/zeromicro/go-zero/rest/httpx"
)

// 自定义校验标签
const (
	// tagNotBlank 去除首尾空白后不能为空
	tagNotBlank = "notblank"
	// tagPositiveInt 字符串形式的正整数，用于 path 变量
	tagPositiveInt = "positiveint"
	// tagDateTime 按项目统一时间格式校验
	tagDateTime = "datetime"
	// tagSearchMode 搜索模式枚举，大小写与首尾空白不敏感
	tagSearchMode = "searchmode"
	// tagMaxRunes 按字符数限制长度，避免中文按字节误判
	tagMaxRunes = "maxrunes"
	// tagNotBefore 不早于同级的指定时间字段
	tagNotBefore = "notbefore"
)

// 请求参数名来源标签，错误消息优先取这些标签声明的名称
var requestNameTags = []string{"json", "form", "path", "header"}

// customTranslation 自定义标签的中文消息，needParam 表示消息中带 {1} 占位
type customTranslation struct {
	tag       string
	message   string
	needParam bool
}

// RequestValidator 实现 httpx.Validator，把校验失败转换为项目统一的业务异常
type RequestValidator struct {
	validate   *validator.Validate
	translator ut.Translator
}

// NewRequestValidator 创建校验器，注册自定义规则与中文消息
func NewRequestValidator() (*RequestValidator, error) {
	zhLocale := zh.New()
	translator, ok := ut.New(zhLocale, zhLocale).GetTranslator(zhLocale.Locale())
	if !ok {
		return nil, errors.New(constants.VALIDATOR_TRANSLATOR_INIT_FAIL)
	}

	validate := validator.New()
	validate.RegisterTagNameFunc(requestFieldName)

	if err := registerCustomRules(validate); err != nil {
		return nil, err
	}
	if err := zhtranslations.RegisterDefaultTranslations(validate, translator); err != nil {
		return nil, fmt.Errorf(constants.VALIDATOR_TRANSLATOR_INIT_FAIL, err)
	}
	if err := registerCustomTranslations(validate, translator); err != nil {
		return nil, err
	}

	return &RequestValidator{validate: validate, translator: translator}, nil
}

// InitValidator 向 go-zero 注册全局校验器，使 httpx.Parse 在解析后自动校验请求
func InitValidator() error {
	requestValidator, err := NewRequestValidator()
	if err != nil {
		return err
	}
	httpx.SetValidator(requestValidator)

	return nil
}

// Validate 实现 httpx.Validator 接口
func (v *RequestValidator) Validate(_ *http.Request, data any) error {
	if data == nil {
		return nil
	}

	if err := v.validate.Struct(data); err != nil {
		return v.toBusinessError(err)
	}

	return nil
}

// toBusinessError 把校验错误转为业务异常，只取第一条以保持「一次只报一个错」的响应形态
func (v *RequestValidator) toBusinessError(err error) error {
	var validationErrs validator.ValidationErrors
	if !errors.As(err, &validationErrs) || len(validationErrs) == 0 {
		return exceptions.NewBadRequestError(constants.PARAM_ERR, err.Error())
	}

	return exceptions.NewBadRequestErrorSame(validationErrs[0].Translate(v.translator))
}

// requestFieldName 取请求参数名而非 Go 字段名进入错误消息
func requestFieldName(field reflect.StructField) string {
	for _, tag := range requestNameTags {
		name := strings.Split(field.Tag.Get(tag), ",")[0]
		if name != "" && name != "-" {
			return name
		}
	}

	return field.Name
}

// registerCustomRules 注册项目自定义校验规则
func registerCustomRules(validate *validator.Validate) error {
	rules := map[string]validator.Func{
		tagNotBlank:    validateNotBlank,
		tagPositiveInt: validatePositiveInt,
		tagDateTime:    validateDateTime,
		tagSearchMode:  validateSearchMode,
		tagMaxRunes:    validateMaxRunes,
		tagNotBefore:   validateNotBefore,
	}

	for tag, rule := range rules {
		if err := validate.RegisterValidation(tag, rule); err != nil {
			return fmt.Errorf(constants.VALIDATOR_RULE_REGISTER_FAIL, tag, err)
		}
	}

	return nil
}

// validateNotBlank 去除首尾空白后仍不能为空，避免仅空白字符通过必填校验
func validateNotBlank(fl validator.FieldLevel) bool {
	return strings.TrimSpace(fl.Field().String()) != ""
}

// validatePositiveInt 字符串必须能解析为正整数
func validatePositiveInt(fl validator.FieldLevel) bool {
	parsed, err := strconv.ParseInt(strings.TrimSpace(fl.Field().String()), 10, 64)

	return err == nil && parsed > 0
}

// validateDateTime 必须符合项目统一的时间格式
func validateDateTime(fl validator.FieldLevel) bool {
	value := strings.TrimSpace(fl.Field().String())
	if value == "" {
		return false
	}

	_, err := time.ParseInLocation(constants.DateTimeFormat, value, time.Local)

	return err == nil
}

// validateSearchMode 搜索模式枚举，空值放行，大小写与首尾空白不敏感
func validateSearchMode(fl validator.FieldLevel) bool {
	switch strings.ToLower(strings.TrimSpace(fl.Field().String())) {
	case "", "keyword", "hybrid", "graph":
		return true
	default:
		return false
	}
}

// validateMaxRunes 按字符数限制长度，参数为上限
func validateMaxRunes(fl validator.FieldLevel) bool {
	limit, err := strconv.Atoi(fl.Param())
	if err != nil {
		return false
	}

	return utf8.RuneCountInString(strings.TrimSpace(fl.Field().String())) <= limit
}

// validateNotBefore 不得早于同级指定字段，任一字段缺失或格式非法时交由其他规则判定
func validateNotBefore(fl validator.FieldLevel) bool {
	endTime, ok := parseFieldTime(fl.Field())
	if !ok {
		return true
	}

	startTime, ok := parseFieldTime(fl.Parent().FieldByName(fl.Param()))
	if !ok {
		return true
	}

	return !startTime.After(endTime)
}

// parseFieldTime 解析字符串或字符串指针字段为时间
func parseFieldTime(field reflect.Value) (time.Time, bool) {
	if !field.IsValid() {
		return time.Time{}, false
	}
	if field.Kind() == reflect.Ptr {
		if field.IsNil() {
			return time.Time{}, false
		}
		field = field.Elem()
	}
	if field.Kind() != reflect.String {
		return time.Time{}, false
	}

	value := strings.TrimSpace(field.String())
	if value == "" {
		return time.Time{}, false
	}

	parsed, err := time.ParseInLocation(constants.DateTimeFormat, value, time.Local)
	if err != nil {
		return time.Time{}, false
	}

	return parsed, true
}

// registerCustomTranslations 注册自定义规则的中文消息
func registerCustomTranslations(validate *validator.Validate, translator ut.Translator) error {
	translations := []customTranslation{
		{tag: tagNotBlank, message: constants.VALIDATOR_NOT_BLANK_MESSAGE},
		{tag: tagPositiveInt, message: constants.VALIDATOR_POSITIVE_INT_MESSAGE},
		{tag: tagDateTime, message: constants.VALIDATOR_DATETIME_MESSAGE},
		{tag: tagSearchMode, message: constants.VALIDATOR_SEARCH_MODE_MESSAGE},
		{tag: tagMaxRunes, message: constants.VALIDATOR_MAX_RUNES_MESSAGE, needParam: true},
		{tag: tagNotBefore, message: constants.VALIDATOR_NOT_BEFORE_MESSAGE},
	}

	for _, item := range translations {
		if err := registerTranslation(validate, translator, item); err != nil {
			return err
		}
	}

	return nil
}

// registerTranslation 为单个自定义标签注册消息，占位符数量与消息模板保持一致
func registerTranslation(validate *validator.Validate, translator ut.Translator, item customTranslation) error {
	err := validate.RegisterTranslation(item.tag, translator, func(ut ut.Translator) error {
		return ut.Add(item.tag, item.message, true)
	}, func(ut ut.Translator, fe validator.FieldError) string {
		args := []string{fe.Field()}
		if item.needParam {
			args = append(args, fe.Param())
		}

		translated, err := ut.T(item.tag, args...)
		if err != nil {
			return fe.Error()
		}

		return translated
	})
	if err != nil {
		return fmt.Errorf(constants.VALIDATOR_RULE_REGISTER_FAIL, item.tag, err)
	}

	return nil
}
