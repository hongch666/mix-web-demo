package utils_test

import (
	"path/filepath"
	"testing"

	"app/common/utils"
	"app/internal/boot"

	"github.com/joho/godotenv"
	"github.com/zeromicro/go-zero/core/logx"
)

func initTestInternalTokenUtil(t *testing.T) *utils.InternalTokenUtil {
	t.Helper()

	_ = godotenv.Load(filepath.Join("..", "..", ".env"))

	configFile := filepath.Join("..", "..", "etc", "application.yaml")
	c := boot.LoadConfig(configFile)

	if err := utils.InitInternalTokenUtil(c.InternalToken.Secret, c.InternalToken.Expiration); err != nil {
		t.Fatalf("初始化内部令牌工具失败: %v", err)
	}

	tokenUtil, err := utils.GetTokenUtil()
	if err != nil {
		t.Fatalf("获取内部令牌工具失败: %v", err)
	}
	return tokenUtil
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
	token, err := tokenUtil.GenerateInternalToken(10001, "gozero")
	if err != nil {
		t.Fatalf("生成待校验Token失败: %v", err)
	}

	_, err = tokenUtil.ValidateInternalToken(token)
	if err != nil {
		t.Fatalf("校验内部Token失败: %v", err)
	}
}
