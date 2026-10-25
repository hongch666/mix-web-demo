package middleware

import (
	"io"
	"net/http"
	"net/http/httptest"
	"reflect"
	"strings"
	"testing"

	"github.com/stretchr/testify/assert"
)

// 验证该测试场景的预期行为

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

// 验证该测试场景的预期行为

func TestExtractQueryParams(t *testing.T) {
	request := httptest.NewRequest(http.MethodGet, "/items?page=1&tag=a&tag=b", nil)
	want := map[string]any{"page": "1", "tag": []string{"a", "b"}}
	if got := extractQueryParams(request); !reflect.DeepEqual(got, want) {
		t.Fatalf("查询参数 = %#v, want %#v", got, want)
	}
}

// 验证该测试场景的预期行为

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

// 验证该测试场景的预期行为

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

// 验证请求体按排除字段脱敏，且嵌套、切片与非字符串值都得到正确处理

func TestSanitizeBodyWithExcludeFields(t *testing.T) {
	tests := []struct {
		name          string
		input         any
		excludeFields []string
		expected      any
	}{
		{
			name: "should mask simple sensitive fields in map",
			input: map[string]any{
				"username": "john",
				"password": "secret123",
				"email":    "john@example.com",
			},
			excludeFields: []string{"password"},
			expected: map[string]any{
				"username": "john",
				"password": "******",
				"email":    "john@example.com",
			},
		},
		{
			name: "should mask multiple sensitive fields",
			input: map[string]any{
				"username": "john",
				"password": "secret123",
				"captcha":  "654321",
				"token":    "abc123xyz",
			},
			excludeFields: []string{"password", "captcha", "token"},
			expected: map[string]any{
				"username": "john",
				"password": "******",
				"captcha":  "******",
				"token":    "******",
			},
		},
		{
			name: "should be case insensitive for field names",
			input: map[string]any{
				"Username": "john",
				"PASSWORD": "secret123",
				"Email":    "john@example.com",
			},
			excludeFields: []string{"password"},
			expected: map[string]any{
				"Username": "john",
				"PASSWORD": "******",
				"Email":    "john@example.com",
			},
		},
		{
			name: "should handle nested map structures",
			input: map[string]any{
				"user": map[string]any{
					"username": "john",
					"password": "secret123",
					"profile": map[string]any{
						"email":   "john@example.com",
						"api_key": "key123",
					},
				},
			},
			excludeFields: []string{"password", "api_key"},
			expected: map[string]any{
				"user": map[string]any{
					"username": "john",
					"password": "******",
					"profile": map[string]any{
						"email":   "john@example.com",
						"api_key": "******",
					},
				},
			},
		},
		{
			name: "should handle slice with map elements",
			input: map[string]any{
				"users": []any{
					map[string]any{
						"username": "john",
						"password": "secret123",
					},
					map[string]any{
						"username": "jane",
						"password": "secret456",
					},
				},
			},
			excludeFields: []string{"password"},
			expected: map[string]any{
				"users": []any{
					map[string]any{
						"username": "john",
						"password": "******",
					},
					map[string]any{
						"username": "jane",
						"password": "******",
					},
				},
			},
		},
		{
			name: "should return unchanged when excludeFields is empty",
			input: map[string]any{
				"username": "john",
				"password": "secret123",
			},
			excludeFields: []string{},
			expected: map[string]any{
				"username": "john",
				"password": "secret123",
			},
		},
		{
			name:          "should return unchanged when data is nil",
			input:         nil,
			excludeFields: []string{"password"},
			expected:      nil,
		},
		{
			name: "should preserve primitive types",
			input: map[string]any{
				"count":    42,
				"active":   true,
				"score":    3.14,
				"message":  "hello",
				"password": "secret123",
			},
			excludeFields: []string{"password"},
			expected: map[string]any{
				"count":    42,
				"active":   true,
				"score":    3.14,
				"message":  "hello",
				"password": "******",
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := sanitizeBody(tt.input, tt.excludeFields)
			assert.Equal(t, tt.expected, result)
		})
	}
}

// 验证查询参数按排除字段脱敏

func TestSanitizeQueryParams(t *testing.T) {
	tests := []struct {
		name          string
		input         map[string]any
		excludeFields []string
		expected      map[string]any
	}{
		{
			name: "should mask sensitive query params",
			input: map[string]any{
				"page":   "1",
				"search": "test",
				"token":  "abc123xyz",
			},
			excludeFields: []string{"token"},
			expected: map[string]any{
				"page":   "1",
				"search": "test",
				"token":  "******",
			},
		},
		{
			name: "should mask multiple sensitive params",
			input: map[string]any{
				"page":  "1",
				"token": "abc123xyz",
				"code":  "654321",
			},
			excludeFields: []string{"token", "code"},
			expected: map[string]any{
				"page":  "1",
				"token": "******",
				"code":  "******",
			},
		},
		{
			name: "should be case insensitive for param names",
			input: map[string]any{
				"Page":   "1",
				"TOKEN":  "abc123xyz",
				"Search": "test",
			},
			excludeFields: []string{"token"},
			expected: map[string]any{
				"Page":   "1",
				"TOKEN":  "******",
				"Search": "test",
			},
		},
		{
			name:          "should handle empty params",
			input:         map[string]any{},
			excludeFields: []string{"token"},
			expected:      map[string]any{},
		},
		{
			name:          "should return unchanged when excludeFields is empty",
			input:         map[string]any{"token": "abc123"},
			excludeFields: []string{},
			expected:      map[string]any{"token": "abc123"},
		},
		{
			name:          "should return unchanged when params is nil",
			input:         nil,
			excludeFields: []string{"token"},
			expected:      nil,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := sanitizeQueryParams(tt.input, tt.excludeFields)
			assert.Equal(t, tt.expected, result)
		})
	}
}

// 验证递归脱敏覆盖深层嵌套、数组的数组与非容器值

func TestDoSanitizeRecursive(t *testing.T) {
	excludeSet := map[string]struct{}{
		"password": {},
		"token":    {},
	}

	t.Run("should handle deeply nested structures", func(t *testing.T) {
		input := map[string]any{
			"level1": map[string]any{
				"level2": map[string]any{
					"level3": map[string]any{
						"password": "secret",
						"username": "john",
					},
				},
			},
		}

		result := doSanitize(input, excludeSet)

		expected := map[string]any{
			"level1": map[string]any{
				"level2": map[string]any{
					"level3": map[string]any{
						"password": "******",
						"username": "john",
					},
				},
			},
		}

		assert.Equal(t, expected, result)
	})

	t.Run("should handle array of arrays", func(t *testing.T) {
		input := []any{
			[]any{
				map[string]any{
					"password": "secret1",
				},
				map[string]any{
					"password": "secret2",
				},
			},
		}

		result := doSanitize(input, excludeSet)

		expected := []any{
			[]any{
				map[string]any{
					"password": "******",
				},
				map[string]any{
					"password": "******",
				},
			},
		}

		assert.Equal(t, expected, result)
	})

	t.Run("should preserve non-string, non-map, non-slice values", func(t *testing.T) {
		input := []any{42, true, 3.14, nil, "string"}
		result := doSanitize(input, excludeSet)
		assert.Equal(t, input, result)
	})
}

// 验证脱敏的边界输入：空数据、排除字段缺失、嵌套中的 nil

func TestSanitizeBodyEdgeCases(t *testing.T) {
	t.Run("should handle empty map", func(t *testing.T) {
		result := sanitizeBody(map[string]any{}, []string{"password"})
		assert.Equal(t, map[string]any{}, result)
	})

	t.Run("should handle map with only excluded fields", func(t *testing.T) {
		input := map[string]any{
			"password": "secret123",
			"token":    "abc123xyz",
		}
		result := sanitizeBody(input, []string{"password", "token"})

		expected := map[string]any{
			"password": "******",
			"token":    "******",
		}
		assert.Equal(t, expected, result)
	})

	t.Run("should handle empty exclude fields with non-empty data", func(t *testing.T) {
		input := map[string]any{
			"username": "john",
			"email":    "john@example.com",
		}
		result := sanitizeBody(input, []string{})
		assert.Equal(t, input, result)
	})

	t.Run("should handle exclude fields not present in data", func(t *testing.T) {
		input := map[string]any{
			"username": "john",
			"email":    "john@example.com",
		}
		result := sanitizeBody(input, []string{"password", "token", "api_key"})
		assert.Equal(t, input, result)
	})

	t.Run("should preserve nil values in nested structures", func(t *testing.T) {
		input := map[string]any{
			"data": nil,
			"user": map[string]any{
				"password": "secret",
				"extra":    nil,
			},
		}
		result := sanitizeBody(input, []string{"password"})

		expected := map[string]any{
			"data": nil,
			"user": map[string]any{
				"password": "******",
				"extra":    nil,
			},
		}
		assert.Equal(t, expected, result)
	})
}
