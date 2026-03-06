package boot

import (
	"os"
	"regexp"
	"strconv"
	"strings"

	"app/common/utils"
	"app/internal/config"

	"github.com/joho/godotenv"
	"github.com/zeromicro/go-zero/core/conf"
	"github.com/zeromicro/go-zero/core/logx"
)

// expandEnvWithDefaults 展开配置文件中的环境变量，支持 ${VAR:default} 格式
// 对于嵌套结构中的纯数字值加引号，以确保 YAML 解析为字符串
func expandEnvWithDefaults(content string) string {
	lines := strings.Split(content, "\n")
	result := make([]string, 0, len(lines))

	for _, line := range lines {
		result = append(result, expandLineEnv(line))
	}

	return strings.Join(result, "\n")
}

// expandLineEnv 展开单行中的环境变量
func expandLineEnv(line string) string {
	// 获取缩进信息
	indent := getLineIndent(line)
	isNestedField := indent > 0

	// 获取该行的字段名（冒号前的部分）
	colonIdx := strings.Index(line, ":")
	var fieldName string
	if colonIdx > 0 {
		fieldName = strings.TrimSpace(line[:colonIdx])
	}

	// 正则表达式匹配 ${VAR:default} 格式或 ${VAR} 格式
	re := regexp.MustCompile(`\$\{([^}:]+)(?::([^}]*))?\}`)

	return re.ReplaceAllStringFunc(line, func(match string) string {
		parts := re.FindStringSubmatch(match)
		if len(parts) < 2 {
			return match
		}

		varName := parts[1]
		defaultValue := ""
		if len(parts) > 2 {
			defaultValue = parts[2]
		}

		// 优先使用环境变量值，如果不存在则使用默认值
		value := defaultValue
		if envValue, ok := os.LookupEnv(varName); ok {
			value = envValue
		}

		// 对嵌套字段中的纯数字值加引号（不包括 Port 字段和顶层）
		// Port、Expiration 等整数字段不加引号，让 YAML 保持数字类型
		if isNestedField && value != "" && isNumeric(value) {
			// 不对 port、expiration 等字段加引号，这些本应是数字类型
			if strings.ToLower(fieldName) != "port" &&
				strings.ToLower(fieldName) != "expiration" &&
				strings.ToLower(fieldName) != "recency_decay_days" &&
				!strings.HasSuffix(strings.ToLower(fieldName), "_weight") &&
				!strings.HasSuffix(strings.ToLower(fieldName), "_normalized") {
				if !isQuoted(value) {
					value = "\"" + value + "\""
				}
			}
		}

		return value
	})
}

// getLineIndent 获取行的缩进空格数
func getLineIndent(line string) int {
	count := 0
	for _, ch := range line {
		switch ch {
		case ' ':
			count++
		case '\t':
			count += 2
		default:
			return count
		}
	}
	return count
}

// isNumeric 检查值是否为纯数字（整数）
func isNumeric(value string) bool {
	_, err := strconv.ParseInt(value, 10, 64)
	return err == nil
}

// isQuoted 检查值是否已被引号包裹
func isQuoted(value string) bool {
	return (len(value) >= 2 && value[0] == '"' && value[len(value)-1] == '"') ||
		(len(value) >= 2 && value[0] == '\'' && value[len(value)-1] == '\'')
}

// LoadConfig 加载配置，包括环境变量和应用配置
func LoadConfig(configFile string) config.Config {
	// 加载 .env 文件中的环境变量
	_ = godotenv.Load()

	// 读取配置文件内容
	content, err := os.ReadFile(configFile)
	if err != nil {
		logx.Errorf(utils.READ_CONFIG_FILE_ERROR, configFile, err)
		os.Exit(1)
	}

	// 展开环境变量（支持 ${VAR:default} 格式）
	expandedContent := expandEnvWithDefaults(string(content))

	// 解析展开后的配置
	var c config.Config
	if err := conf.LoadFromYamlBytes([]byte(expandedContent), &c); err != nil {
		logx.Errorf(utils.PARSE_CONFIG_FILE_ERROR, configFile, err)
		os.Exit(1)
	}

	return c
}
