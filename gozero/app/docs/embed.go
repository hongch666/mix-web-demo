package docs

import "embed"

// StaticFiles 嵌入所有 Swagger 静态文件，编译进二进制，运行时无需磁盘读取
//
//go:embed swagger.html main.json
var StaticFiles embed.FS
