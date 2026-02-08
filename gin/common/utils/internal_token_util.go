package utils

import (
	"time"

	"github.com/golang-jwt/jwt/v5"
	"github.com/hongch666/mix-web-demo/gin/common/exceptions"
)

// InternalTokenClaims 内部服务令牌声明
type InternalTokenClaims struct {
	UserID      int64  `json:"userId"`
	ServiceName string `json:"serviceName"`
	TokenType   string `json:"tokenType"`
	jwt.RegisteredClaims
}

// InternalTokenUtil 内部服务令牌工具类
type InternalTokenUtil struct {
	secret     string
	expiration int64
}

var tokenUtil *InternalTokenUtil

// InitInternalTokenUtil 初始化内部令牌工具
func InitInternalTokenUtil(secret string, expiration int64) {
	tokenUtil = &InternalTokenUtil{
		secret:     secret,
		expiration: expiration,
	}
	if tokenUtil.secret == "" {
		panic(exceptions.NewBusinessErrorSame(INTERNAL_TOKEN_SECRET_NOT_NULL))
	}
}

// GetTokenUtil 获取内部令牌工具实例
func GetTokenUtil() *InternalTokenUtil {
	if tokenUtil == nil {
		panic(exceptions.NewBusinessErrorSame(INTERNAL_TOKEN_SECRET_NOT_NULL))
	}
	return tokenUtil
}

// GenerateInternalToken 生成内部服务令牌
func (t *InternalTokenUtil) GenerateInternalToken(userID int64, serviceName string) (string, error) {
	now := time.Now()
	expirationTime := now.Add(time.Duration(t.expiration) * time.Millisecond)

	claims := InternalTokenClaims{
		UserID:      userID,
		ServiceName: serviceName,
		TokenType:   "internal",
		RegisteredClaims: jwt.RegisteredClaims{
			ExpiresAt: jwt.NewNumericDate(expirationTime),
			IssuedAt:  jwt.NewNumericDate(now),
			NotBefore: jwt.NewNumericDate(now),
			Subject:   "internal_service_token",
		},
	}

	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	return token.SignedString([]byte(t.secret))
}

// ValidateInternalToken 验证内部令牌
func (t *InternalTokenUtil) ValidateInternalToken(tokenString string) (*InternalTokenClaims, error) {
	claims := &InternalTokenClaims{}
	token, err := jwt.ParseWithClaims(tokenString, claims, func(token *jwt.Token) (any, error) {
		return []byte(t.secret), nil
	})

	if err != nil {
		return nil, err
	}

	if !token.Valid {
		return nil, jwt.ErrSignatureInvalid
	}

	return claims, nil
}

// ExtractUserID 从令牌中提取用户ID
func (claims *InternalTokenClaims) ExtractUserID() int64 {
	return claims.UserID
}

// ExtractServiceName 从令牌中提取服务名称
func (claims *InternalTokenClaims) ExtractServiceName() string {
	return claims.ServiceName
}
