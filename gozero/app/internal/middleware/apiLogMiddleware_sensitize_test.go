package middleware

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

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

func TestEdgeCases(t *testing.T) {
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
