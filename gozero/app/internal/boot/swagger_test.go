package boot

import (
	"encoding/json"
	"path"
	"testing"

	"app/docs"
)

// TestEmbeddedSwaggerResourcesAreReadable 校验页面、文档与 swagger-ui 静态资源都已嵌入且非空，路由按文件名读取 embed.FS，文件缺失或改名会让页面返回 500，表现为 Swagger 白屏
func TestEmbeddedSwaggerResourcesAreReadable(t *testing.T) {
	names := []string{
		"swagger.html",
		"openapi.json",
		"swagger-ui.css",
		"swagger-ui-bundle.js",
		"swagger-ui-standalone-preset.js",
		"favicon-16x16.png",
		"favicon-32x32.png",
	}

	for _, name := range names {
		content, err := docs.StaticFiles.ReadFile(name)
		if err != nil {
			t.Fatalf("内嵌资源缺失: %s, err: %v", name, err)
		}
		if len(content) == 0 {
			t.Fatalf("内嵌资源为空: %s", name)
		}
	}
}

// TestSwaggerContentTypesCoverEmbeddedResources 校验每类内嵌资源都有显式 Content-Type，缺 Content-Type 或类型不对时浏览器会拒绝执行 swagger-ui-bundle.js，页面同样白屏
func TestSwaggerContentTypesCoverEmbeddedResources(t *testing.T) {
	cases := map[string]string{
		"swagger.html":                    "text/html; charset=utf-8",
		"openapi.json":                    "application/json; charset=utf-8",
		"swagger-ui.css":                  "text/css; charset=utf-8",
		"swagger-ui-bundle.js":            "text/javascript; charset=utf-8",
		"swagger-ui-standalone-preset.js": "text/javascript; charset=utf-8",
		"favicon-32x32.png":               "image/png",
	}

	for name, want := range cases {
		got, ok := swaggerContentTypes[path.Ext(name)]
		if !ok || got != want {
			t.Fatalf("%s 的 Content-Type = %q, 期望 %q", name, got, want)
		}
	}
}

// TestEmbeddedOpenAPIDocumentUsesVersionSupportedBySwaggerUI 校验产物版本与空数据类型写法一致，内嵌 swagger-ui 为 5.x：保留 3.1 才能表达 type: "null"，降到 3.0 会让该 schema 非法
func TestEmbeddedOpenAPIDocumentUsesVersionSupportedBySwaggerUI(t *testing.T) {
	content, err := docs.StaticFiles.ReadFile("openapi.json")
	if err != nil {
		t.Fatal(err)
	}

	var document map[string]any
	if err = json.Unmarshal(content, &document); err != nil {
		t.Fatalf("产物不是合法 JSON: %v", err)
	}

	if version, _ := document["openapi"].(string); version != "3.1.0" {
		t.Fatalf("产物规范版本 = %q, 期望 3.1.0", document["openapi"])
	}

	if !containsNullType(document) {
		t.Fatal("产物缺少 type: null 的空数据 schema，空响应无法在文档中表达")
	}
}

// containsNullType 递归查找 type: null 的 schema，用于确认空数据声明仍在产物中
func containsNullType(value any) bool {
	switch typed := value.(type) {
	case map[string]any:
		if typed["type"] == "null" {
			return true
		}
		for _, item := range typed {
			if containsNullType(item) {
				return true
			}
		}
	case []any:
		for _, item := range typed {
			if containsNullType(item) {
				return true
			}
		}
	}
	return false
}
