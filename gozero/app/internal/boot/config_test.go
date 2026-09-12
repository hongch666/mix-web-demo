package boot

import (
	"strings"
	"testing"
)

func TestExpandEnvWithDefaultsPrefersEnvValue(t *testing.T) {
	t.Setenv("CONFIG_TEST_HOST", "10.0.0.1")

	expanded := expandEnvWithDefaults("Host: ${CONFIG_TEST_HOST:127.0.0.1}\nPort: ${CONFIG_TEST_PORT:8082}\n")

	if !strings.Contains(expanded, "Host: 10.0.0.1") {
		t.Fatalf("环境变量未被优先使用: %s", expanded)
	}
	if !strings.Contains(expanded, "Port: 8082") {
		t.Fatalf("默认值未被应用: %s", expanded)
	}
}

func TestExpandLineEnvQuotesNestedNumericValue(t *testing.T) {
	// 嵌套结构中的非白名单数字字段需要保持字符串类型
	quoted := expandLineEnv("    some_count: ${SOME_COUNT:5}")
	if !strings.Contains(quoted, "\"5\"") {
		t.Fatalf("嵌套数字字段未加引号: %s", quoted)
	}

	// port 属白名单字段，应保持数字类型不加引号
	portLine := expandLineEnv("    port: ${DB_PORT:3306}")
	if strings.Contains(portLine, "\"3306\"") {
		t.Fatalf("port 字段不应被加引号: %s", portLine)
	}
}

func TestNormalizeModeValueMapsProdAlias(t *testing.T) {
	if got := normalizeModeValue("mode", "prod"); got != "pro" {
		t.Fatalf("prod 未转换为 pro: %s", got)
	}
	if got := normalizeModeValue("mode", "dev"); got != "dev" {
		t.Fatalf("dev 不应被修改: %s", got)
	}
	if got := normalizeModeValue("other", "prod"); got != "prod" {
		t.Fatalf("非 mode 字段不应被修改: %s", got)
	}
}

func TestIsNumericAndIsQuoted(t *testing.T) {
	if !isNumeric("8082") || isNumeric("8082a") {
		t.Fatal("isNumeric 判断错误")
	}
	if !isQuoted("\"x\"") || !isQuoted("'x'") || isQuoted("x") {
		t.Fatal("isQuoted 判断错误")
	}
}
