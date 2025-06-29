package utils

import (
	"time"

	"github.com/golang-jwt/jwt/v5"
)

var JwtSecret = []byte("hcsy")

// 生成JWT
func GenerateToken(username string) (string, error) {
	// var jwtSecret = []byte("hcsy")
	// 创建一个新的令牌对象，指定签名方法和声明
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, jwt.MapClaims{
		"username": username,
		"exp":      time.Now().Add(time.Hour * 2).Unix(), // 2小时后过期
	})

	// 使用密钥字符串对token进行签名，并获取完整的编码后的字符串token
	tokenString, err := token.SignedString(JwtSecret)
	if err != nil {
		return "", err
	}
	return tokenString, nil
}
