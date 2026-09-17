package types

import "testing"

func TestSearchArticlesReqValidate(t *testing.T) {
	validStart := "2026-09-01 00:00:00"
	validEnd := "2026-09-17 23:59:59"
	invalidTime := "2026/09/01"
	zeroUserID := uint64(0)
	invalidMode := "semantic"

	tests := []struct {
		name    string
		req     SearchArticlesReq
		wantErr bool
	}{
		{name: "合法请求", req: SearchArticlesReq{Page: 1, Size: 10, StartDate: &validStart, EndDate: &validEnd}},
		{name: "用户ID必须大于零", req: SearchArticlesReq{Page: 1, Size: 10, UserId: &zeroUserID}, wantErr: true},
		{name: "页码必须大于零", req: SearchArticlesReq{Page: 0, Size: 10}, wantErr: true},
		{name: "每页数量必须大于零", req: SearchArticlesReq{Page: 1, Size: 0}, wantErr: true},
		{name: "开始时间格式错误", req: SearchArticlesReq{Page: 1, Size: 10, StartDate: &invalidTime}, wantErr: true},
		{name: "开始时间晚于结束时间", req: SearchArticlesReq{Page: 1, Size: 10, StartDate: &validEnd, EndDate: &validStart}, wantErr: true},
		{name: "搜索模式不支持", req: SearchArticlesReq{Page: 1, Size: 10, Mode: &invalidMode}, wantErr: true},
	}

	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			err := test.req.Validate()
			if (err != nil) != test.wantErr {
				t.Fatalf("Validate() error = %v, wantErr %v", err, test.wantErr)
			}
		})
	}
}

func TestGetSearchHistoryReqValidate(t *testing.T) {
	tests := []struct {
		name    string
		userID  string
		wantErr bool
	}{
		{name: "合法用户ID", userID: "7"},
		{name: "空用户ID", userID: " ", wantErr: true},
		{name: "非数字用户ID", userID: "user", wantErr: true},
		{name: "零用户ID", userID: "0", wantErr: true},
		{name: "负数用户ID", userID: "-1", wantErr: true},
	}

	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			err := (&GetSearchHistoryReq{UserId: test.userID}).Validate()
			if (err != nil) != test.wantErr {
				t.Fatalf("Validate() error = %v, wantErr %v", err, test.wantErr)
			}
		})
	}
}

func TestSearchEnhancementOptions(t *testing.T) {
	keywordMode := " keyword "
	graphMode := "graph"
	disabled := false
	keyword := "文章"

	if got := NormalizeSearchMode(&SearchArticlesReq{}); got != "hybrid" {
		t.Errorf("默认搜索模式 = %q, 期望 hybrid", got)
	}
	if IsVectorEnhanceEnabled(&SearchArticlesReq{Mode: &keywordMode}, keyword) {
		t.Error("keyword 模式不应该启用向量增强")
	}
	if !IsVectorEnhanceEnabled(&SearchArticlesReq{Mode: &graphMode}, keyword) {
		t.Error("graph 模式默认应该启用向量增强")
	}
	if IsGraphEnhanceEnabled(&SearchArticlesReq{EnableGraph: &disabled}) {
		t.Error("显式关闭时不应该启用图谱增强")
	}
	if !IsExplainEnabled(&SearchArticlesReq{}) {
		t.Error("默认应该返回搜索解释")
	}
}
