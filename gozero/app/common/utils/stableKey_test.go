package utils

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

// TestStableKeyIsOrderSensitive 校验片段顺序不同会得到不同摘要
func TestStableKeyIsOrderSensitive(t *testing.T) {
	assert.NotEqual(t, StableKey("a", "b"), StableKey("b", "a"))
}

// TestStableKeyIsStable 校验相同入参多次调用结果一致
func TestStableKeyIsStable(t *testing.T) {
	assert.Equal(t, StableKey("keyword", "1", "10"), StableKey("keyword", "1", "10"))
}

// TestStableKeySeparatesSegments 校验片段边界不会被拼接吞掉
func TestStableKeySeparatesSegments(t *testing.T) {
	assert.NotEqual(t, StableKey("ab", ""), StableKey("a", "b"))
}

// TestStableKeyEmptyInput 校验空入参也返回固定长度的十六进制摘要
func TestStableKeyEmptyInput(t *testing.T) {
	assert.Len(t, StableKey(), 64)
}
