package utils_test

import (
	"os"
	"path/filepath"
	"testing"

	"app/common/utils"
	"app/internal/boot"

	"github.com/zeromicro/go-zero/core/logx"
)

func initTestInternalTokenUtil(t *testing.T) *utils.InternalTokenUtil {
	t.Helper()

	configFile := filepath.Join("..", "..", "etc", "application.yaml")
	c := boot.LoadConfig(configFile)

	utils.InitInternalTokenUtil(c.InternalToken.Secret, c.InternalToken.Expiration)

	return utils.GetTokenUtil()
}

func TestGenerateInternalToken(t *testing.T) {
	tokenUtil := initTestInternalTokenUtil(t)
	userID := int64(10001)
	serviceName := "gozero"

	token, err := tokenUtil.GenerateInternalToken(userID, serviceName)
	if err != nil {
		t.Fatalf("生成内部Token失败: %v", err)
	}
	if token == "" {
		t.Fatal("生成的内部Token为空")
	}
	logx.Infof("生成的内部Token: %s", token)
}

func TestValidateInternalToken(t *testing.T) {
	tokenUtil := initTestInternalTokenUtil(t)
	token := mustGetEnv(t, "INTERNAL_TOKEN_TEST_TOKEN")

	_, err := tokenUtil.ValidateInternalToken(token)
	if err != nil {
		t.Fatalf("校验内部Token失败: %v", err)
	}
}

func mustGetEnv(t *testing.T, key string) string {
	t.Helper()

	value := os.Getenv(key)
	if value == "" {
		t.Fatalf("环境变量 %s 不能为空", key)
	}
	return value
}
