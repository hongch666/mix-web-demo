package validation

import (
	"strings"
	"testing"
)

// 验证该测试场景的预期行为

func TestRequestValidatorBuiltinRules(t *testing.T) {
	requestValidator, err := NewRequestValidator()
	if err != nil {
		t.Fatalf("创建校验器失败: %v", err)
	}

	zeroInt := int64(0)
	negativeInt := int64(-5)
	positiveInt := int64(7)

	tests := []struct {
		name    string
		data    any
		wantMsg string
	}{
		{
			name: "正整数通过",
			data: struct {
				Id int64 `json:"id" validate:"gt=0"`
			}{Id: positiveInt},
		},
		{
			name: "零被拒绝",
			data: struct {
				Id int64 `json:"id" validate:"gt=0"`
			}{Id: 0},
			wantMsg: "必须大于",
		},
		{
			name: "负数被拒绝",
			data: struct {
				Id int64 `json:"id" validate:"gt=0"`
			}{Id: negativeInt},
			wantMsg: "必须大于",
		},
		{
			name: "可选字段缺省通过",
			data: struct {
				Id *int64 `json:"id" validate:"omitempty,gt=0"`
			}{Id: nil},
		},
		{
			name: "可选字段为零被拒绝",
			data: struct {
				Id *int64 `json:"id" validate:"omitempty,gt=0"`
			}{Id: &zeroInt},
			wantMsg: "必须大于",
		},
		{
			name: "可选字段为正数通过",
			data: struct {
				Id *int64 `json:"id" validate:"omitempty,gt=0"`
			}{Id: &positiveInt},
		},
	}

	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			assertValidateResult(t, requestValidator, test.data, test.wantMsg)
		})
	}
}

// 验证该测试场景的预期行为

func TestRequestValidatorCustomRules(t *testing.T) {
	requestValidator, err := NewRequestValidator()
	if err != nil {
		t.Fatalf("创建校验器失败: %v", err)
	}

	blankMode := "  "
	keywordMode := " KEYWORD "
	invalidMode := "SEMANTIC"
	validStart := "2026-09-01 00:00:00"
	validEnd := "2026-09-02 00:00:00"
	reversedStart := "2026-09-03 00:00:00"
	invalidTime := "2026/09/01"
	blankTime := "   "

	tests := []struct {
		name    string
		data    any
		wantMsg string
	}{
		{
			name: "空白内容被拒绝",
			data: struct {
				Content string `json:"content" validate:"notblank"`
			}{Content: "  \n\t "},
			wantMsg: "content不能为空",
		},
		{
			name: "非空内容通过",
			data: struct {
				Content string `json:"content" validate:"notblank"`
			}{Content: "你好"},
		},
		{
			name: "字符串正整数通过",
			data: struct {
				UserId string `json:"user_id" validate:"positiveint"`
			}{UserId: " 7 "},
		},
		{
			name: "字符串零被拒绝",
			data: struct {
				UserId string `json:"user_id" validate:"positiveint"`
			}{UserId: "0"},
			wantMsg: "必须是正整数",
		},
		{
			name: "字符串负数被拒绝",
			data: struct {
				UserId string `json:"user_id" validate:"positiveint"`
			}{UserId: "-1"},
			wantMsg: "必须是正整数",
		},
		{
			name: "非数字被拒绝",
			data: struct {
				UserId string `json:"user_id" validate:"positiveint"`
			}{UserId: "user"},
			wantMsg: "必须是正整数",
		},
		{
			name: "合法时间通过",
			data: struct {
				StartDate *string `json:"start_date" validate:"omitempty,notblank,datetime"`
			}{StartDate: &validStart},
		},
		{
			name: "时间格式非法被拒绝",
			data: struct {
				StartDate *string `json:"start_date" validate:"omitempty,notblank,datetime"`
			}{StartDate: &invalidTime},
			wantMsg: "格式必须为",
		},
		{
			name: "非空但为空白的时间被拒绝",
			data: struct {
				StartDate *string `json:"start_date" validate:"omitempty,notblank,datetime"`
			}{StartDate: &blankTime},
			wantMsg: "start_date不能为空",
		},
		{
			name: "搜索模式大小写与空白不敏感",
			data: struct {
				Mode *string `json:"mode" validate:"omitempty,searchmode"`
			}{Mode: &keywordMode},
		},
		{
			name: "搜索模式空白视为缺省",
			data: struct {
				Mode *string `json:"mode" validate:"omitempty,searchmode"`
			}{Mode: &blankMode},
		},
		{
			name: "搜索模式非法被拒绝",
			data: struct {
				Mode *string `json:"mode" validate:"omitempty,searchmode"`
			}{Mode: &invalidMode},
			wantMsg: "搜索模式参数无效",
		},
		{
			name: "字符数恰好达到上限通过",
			data: struct {
				Text string `json:"text" validate:"maxrunes=3"`
			}{Text: strings.Repeat("张", 3)},
		},
		{
			name: "按字符数而非字节数判定超长",
			data: struct {
				Text string `json:"text" validate:"maxrunes=3"`
			}{Text: strings.Repeat("张", 4)},
			wantMsg: "长度不能超过3个字符",
		},
		{
			name: "时间区间顺序正确通过",
			data: struct {
				Start *string `json:"start_date" validate:"omitempty,notblank,datetime"`
				End   *string `json:"end_date" validate:"omitempty,notblank,datetime,notbefore=Start"`
			}{Start: &validStart, End: &validEnd},
		},
		{
			name: "开始时间晚于结束时间被拒绝",
			data: struct {
				Start *string `json:"start_date" validate:"omitempty,notblank,datetime"`
				End   *string `json:"end_date" validate:"omitempty,notblank,datetime,notbefore=Start"`
			}{Start: &reversedStart, End: &validEnd},
			wantMsg: "不能晚于",
		},
		{
			name: "仅有结束时间时通过",
			data: struct {
				Start *string `json:"start_date" validate:"omitempty,notblank,datetime"`
				End   *string `json:"end_date" validate:"omitempty,notblank,datetime,notbefore=Start"`
			}{End: &validEnd},
		},
	}

	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			assertValidateResult(t, requestValidator, test.data, test.wantMsg)
		})
	}
}

// 验证该测试场景的预期行为

func TestRequestValidatorNilData(t *testing.T) {
	requestValidator, err := NewRequestValidator()
	if err != nil {
		t.Fatalf("创建校验器失败: %v", err)
	}

	if err := requestValidator.Validate(nil, nil); err != nil {
		t.Fatalf("空数据不应报错, 实际错误: %v", err)
	}
}

func assertValidateResult(t *testing.T, requestValidator *RequestValidator, data any, wantMsg string) {
	t.Helper()

	err := requestValidator.Validate(nil, data)
	if wantMsg == "" {
		if err != nil {
			t.Fatalf("期望校验通过, 实际错误: %v", err)
		}
		return
	}

	if err == nil {
		t.Fatal("期望校验失败, 实际通过")
	}
	if !strings.Contains(err.Error(), wantMsg) {
		t.Errorf("错误消息 %q 未包含期望片段 %q", err.Error(), wantMsg)
	}
}
