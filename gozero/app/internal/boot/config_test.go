package boot

import (
	"os"
	"strings"
	"testing"

	"app/internal/config"

	"github.com/zeromicro/go-zero/core/conf"
)

// 验证该测试场景的预期行为

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

// 验证该测试场景的预期行为

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

// 验证该测试场景的预期行为

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

// 验证该测试场景的预期行为

func TestIsNumericAndIsQuoted(t *testing.T) {
	if !isNumeric("8082") || isNumeric("8082a") {
		t.Fatal("isNumeric 判断错误")
	}
	if !isQuoted("\"x\"") || !isQuoted("'x'") || isQuoted("x") {
		t.Fatal("isQuoted 判断错误")
	}
}

// 校验 ES DSL 日志开关能从配置文件经环境变量展开后正确装配
// 覆盖 YAML 占位符展开与结构体字段映射，避免开关写错字段名导致静默失效

func TestESDSLLogSwitchLoadedFromConfig(t *testing.T) {
	content, err := os.ReadFile("../../etc/application.yaml")
	if err != nil {
		t.Fatalf("读取配置文件失败: %v", err)
	}

	if !strings.Contains(string(content), "${DB_ES_DSL_LOG_ENABLED:false}") {
		t.Fatal("配置文件缺少 ES DSL 日志开关占位符")
	}

	t.Setenv("DB_ES_DSL_LOG_ENABLED", "true")

	var c config.Config
	if err := conf.LoadFromYamlBytes([]byte(expandEnvWithDefaults(string(content))), &c); err != nil {
		t.Fatalf("解析配置失败: %v", err)
	}

	if !c.Database.ES.DSLLogEnabled {
		t.Fatal("环境变量置为 true 时 ES DSL 日志开关未生效")
	}
}
