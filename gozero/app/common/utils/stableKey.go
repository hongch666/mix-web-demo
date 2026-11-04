package utils

import (
	"crypto/sha256"
	"encoding/hex"
	"strconv"
	"strings"
)

// StableKey 把多个字符串片段按顺序拼成稳定摘要，用于构造缓存键
// 每个片段带长度前缀，避免不同片段组合拼出同一个字符串
func StableKey(parts ...string) string {
	var builder strings.Builder
	for _, part := range parts {
		builder.WriteString(strconv.Itoa(len(part)))
		builder.WriteByte(':')
		builder.WriteString(part)
		builder.WriteByte('|')
	}

	sum := sha256.Sum256([]byte(builder.String()))
	return hex.EncodeToString(sum[:])
}
