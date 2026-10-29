package utils_test

import (
	"fmt"
	"os"
	"path/filepath"
	"testing"

	"app/common/utils"

	"github.com/joho/godotenv"
)

const testInternalTokenSecret = "unit-test-internal-token-secret-32-bytes"

// 验证该测试场景的预期行为

func TestInternalTokenRoundTrip(t *testing.T) {
	_ = godotenv.Load(filepath.Join("..", "..", ".env"))
	secret := os.Getenv("INTERNAL_TOKEN_SECRET")
	if secret == "" {
		secret = testInternalTokenSecret
	}
	tokenUtil, err := utils.NewInternalTokenUtil(secret, 60000)
	if err != nil {
		t.Fatalf("创建内部令牌工具失败: %v", err)
	}

	token, err := tokenUtil.GenerateInternalToken(10001, "gozero")
	if err != nil {
		t.Fatalf("生成内部令牌失败: %v", err)
	}
	fmt.Printf("生成的内部Token: %s\n", token)
	claims, err := tokenUtil.ValidateInternalToken(token)
	if err != nil {
		t.Fatalf("验证内部令牌失败: %v", err)
	}
	if claims.ExtractUserID() != 10001 {
		t.Errorf("UserID = %d, 期望 10001", claims.ExtractUserID())
	}
	if claims.ExtractServiceName() != "gozero" {
		t.Errorf("ServiceName = %q, 期望 gozero", claims.ExtractServiceName())
	}
	if claims.TokenType != "internal" {
		t.Errorf("TokenType = %q, 期望 internal", claims.TokenType)
	}
}

// 验证该测试场景的预期行为

func TestInternalTokenRejectsDifferentSecret(t *testing.T) {
	issuer, err := utils.NewInternalTokenUtil(testInternalTokenSecret, 60000)
	if err != nil {
		t.Fatalf("创建签发工具失败: %v", err)
	}
	token, err := issuer.GenerateInternalToken(10001, "gozero")
	if err != nil {
		t.Fatalf("生成内部令牌失败: %v", err)
	}

	verifier, err := utils.NewInternalTokenUtil("another-unit-test-secret-with-32-bytes", 60000)
	if err != nil {
		t.Fatalf("创建验证工具失败: %v", err)
	}
	if _, err := verifier.ValidateInternalToken(token); err == nil {
		t.Fatal("使用不同密钥签名的令牌应该验证失败")
	}
}

// 验证该测试场景的预期行为

func TestNewInternalTokenUtilRejectsEmptySecret(t *testing.T) {
	if _, err := utils.NewInternalTokenUtil("", 60000); err == nil {
		t.Fatal("空密钥应该创建失败")
	}
}
