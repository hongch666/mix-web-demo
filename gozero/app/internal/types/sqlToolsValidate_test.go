package types

import (
	"strings"
	"testing"

	"app/common/constants"
)

func TestSqlToolsQueryReqValidate(t *testing.T) {
	cases := []struct {
		name         string
		query        string
		wantErr      bool
		wantContains string
	}{
		{
			name:  "合法查询通过",
			query: "SELECT id FROM chat_messages LIMIT 10",
		},
		{
			name:         "空查询被拒绝",
			query:        "",
			wantErr:      true,
			wantContains: "不能为空",
		},
		{
			name:         "仅空白字符被拒绝",
			query:        "  \n\t ",
			wantErr:      true,
			wantContains: "不能为空",
		},
		{
			name:         "超长查询被拒绝",
			query:        strings.Repeat("A", constants.SqlToolsMaxQueryLength+1),
			wantErr:      true,
			wantContains: "长度不能超过",
		},
		{
			name:  "恰好达到长度上限通过",
			query: strings.Repeat("A", constants.SqlToolsMaxQueryLength),
		},
	}

	for _, testCase := range cases {
		t.Run(testCase.name, func(t *testing.T) {
			req := &SqlToolsQueryReq{Query: testCase.query}
			err := req.Validate()

			if !testCase.wantErr {
				if err != nil {
					t.Fatalf("期望校验通过, 实际错误: %v", err)
				}
				return
			}

			if err == nil {
				t.Fatal("期望校验失败, 实际通过")
			}

			if !strings.Contains(err.Error(), testCase.wantContains) {
				t.Errorf("错误消息 %q 未包含期望片段 %q", err.Error(), testCase.wantContains)
			}
		})
	}
}

func TestSqlToolsGetTablesReqValidate(t *testing.T) {
	cases := []struct {
		name         string
		table        string
		wantErr      bool
		wantContains string
	}{
		{
			name:  "空表名合法",
			table: "",
		},
		{
			name:  "白名单表名通过",
			table: "chat_messages",
		},
		{
			name:  "前后空白不影响判定",
			table: "  chat_messages  ",
		},
		{
			name:         "超长表名被拒绝",
			table:        strings.Repeat("t", constants.SqlToolsMaxTableNameLength+1),
			wantErr:      true,
			wantContains: "长度不能超过",
		},
		{
			name:  "恰好达到长度上限通过",
			table: strings.Repeat("t", constants.SqlToolsMaxTableNameLength),
		},
	}

	for _, testCase := range cases {
		t.Run(testCase.name, func(t *testing.T) {
			req := &SqlToolsGetTablesReq{Table: testCase.table}
			err := req.Validate()

			if !testCase.wantErr {
				if err != nil {
					t.Fatalf("期望校验通过, 实际错误: %v", err)
				}
				return
			}

			if err == nil {
				t.Fatal("期望校验失败, 实际通过")
			}

			if !strings.Contains(err.Error(), testCase.wantContains) {
				t.Errorf("错误消息 %q 未包含期望片段 %q", err.Error(), testCase.wantContains)
			}
		})
	}
}
