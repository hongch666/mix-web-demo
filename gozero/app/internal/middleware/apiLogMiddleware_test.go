package middleware

import (
	"io"
	"net/http"
	"net/http/httptest"
	"reflect"
	"strings"
	"testing"
)

func TestApiLogMiddlewarePassesRequestBodyToHandler(t *testing.T) {
	body := `{"name":"test"}`
	request := httptest.NewRequest(http.MethodPost, "/items?page=1", strings.NewReader(body))
	recorder := httptest.NewRecorder()

	handler := NewApiLogMiddleware("测试接口", nil, nil).Handle(func(w http.ResponseWriter, r *http.Request) {
		restored, err := io.ReadAll(r.Body)
		if err != nil {
			t.Fatalf("读取请求体失败: %v", err)
		}
		if string(restored) != body {
			t.Fatalf("handler 收到的请求体 = %q, want %q", string(restored), body)
		}
		w.WriteHeader(http.StatusCreated)
	})
	handler(recorder, request)
	if recorder.Code != http.StatusCreated {
		t.Fatalf("状态码 = %d, want %d", recorder.Code, http.StatusCreated)
	}
}

func TestExtractQueryParams(t *testing.T) {
	request := httptest.NewRequest(http.MethodGet, "/items?page=1&tag=a&tag=b", nil)
	want := map[string]any{"page": "1", "tag": []string{"a", "b"}}
	if got := extractQueryParams(request); !reflect.DeepEqual(got, want) {
		t.Fatalf("查询参数 = %#v, want %#v", got, want)
	}
}

func TestExtractRequestBody(t *testing.T) {
	tests := []struct {
		name string
		body string
		want any
	}{
		{name: "JSON", body: `{"name":"test"}`, want: map[string]any{"name": "test"}},
		{name: "表单", body: "name=test&tag=a&tag=b", want: map[string]any{"name": "test", "tag": []string{"a", "b"}}},
		{name: "原始文本", body: "%invalid", want: "%invalid"},
		{name: "空请求体", want: nil},
	}

	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			request := httptest.NewRequest(http.MethodPost, "/items", strings.NewReader(test.body))
			got := extractRequestBody(request)
			if !reflect.DeepEqual(got, test.want) {
				t.Fatalf("请求体 = %#v, want %#v", got, test.want)
			}
			restored, err := io.ReadAll(request.Body)
			if err != nil {
				t.Fatalf("读取恢复后的请求体失败: %v", err)
			}
			if string(restored) != test.body {
				t.Fatalf("恢复后的请求体 = %q, want %q", string(restored), test.body)
			}
		})
	}
}

func TestParseFormData(t *testing.T) {
	got, err := parseFormData("name=test&tag=a&tag=b")
	if err != nil {
		t.Fatalf("parseFormData() error = %v", err)
	}
	want := map[string]any{"name": "test", "tag": []string{"a", "b"}}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("表单 = %#v, want %#v", got, want)
	}
}
