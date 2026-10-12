package docs

import "embed"

// StaticFiles 嵌入 Swagger 页面、文档与静态资源，编译进二进制，运行时无需磁盘读取
// swagger-ui 资源取自 swagger-ui-dist 5.x：产物声明 OpenAPI 3.1（含 type: null），
// 4.x 版的 Swagger UI 只认 2.0 与 3.0.x，会在页面上直接报无法渲染
//
//go:embed swagger.html openapi.json
//go:embed swagger-ui.css swagger-ui-bundle.js swagger-ui-standalone-preset.js
//go:embed favicon-16x16.png favicon-32x32.png
var StaticFiles embed.FS
