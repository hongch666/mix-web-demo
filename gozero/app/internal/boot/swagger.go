package boot

import (
	"net/http"
	"path"

	"app/common/constants"
	"app/docs"

	"github.com/zeromicro/go-zero/rest"
)

// swaggerContentTypes 内嵌资源的 Content-Type
// 显式声明而不走 mime.TypeByExtension：后者在 Windows 上会读取系统 MIME 注册表，结果不可控
var swaggerContentTypes = map[string]string{
	".html": "text/html; charset=utf-8",
	".json": "application/json; charset=utf-8",
	".css":  "text/css; charset=utf-8",
	".js":   "text/javascript; charset=utf-8",
	".png":  "image/png",
}

// registerSwaggerRoute 注册 Swagger 文档路由
// 页面、文档与 swagger-ui 资源全部通过 go:embed 编译进二进制，无需运行时磁盘读取
func registerSwaggerRoute(server *rest.Server) {
	// /swagger 重定向到 /swagger/index.html
	server.AddRoute(rest.Route{
		Method: http.MethodGet,
		Path:   "/swagger",
		Handler: func(w http.ResponseWriter, r *http.Request) {
			http.Redirect(w, r, "/swagger/index.html", http.StatusMovedPermanently)
		},
	})

	// 路由与内嵌文件名的映射：页面入口是 index.html、文档入口是 doc.json，与磁盘文件名不同
	resources := []struct {
		route    string
		filename string
		notFound string
	}{
		{route: "/swagger/index.html", filename: "swagger.html", notFound: constants.SWAGGER_PAGE_FETCH_FAIL},
		{route: "/swagger/doc.json", filename: "openapi.json", notFound: constants.GET_SWAGGER_FAIL},
		{route: "/swagger/swagger-ui.css", filename: "swagger-ui.css", notFound: constants.GET_SWAGGER_FAIL},
		{route: "/swagger/swagger-ui-bundle.js", filename: "swagger-ui-bundle.js", notFound: constants.GET_SWAGGER_FAIL},
		{route: "/swagger/swagger-ui-standalone-preset.js", filename: "swagger-ui-standalone-preset.js", notFound: constants.GET_SWAGGER_FAIL},
		{route: "/swagger/favicon-16x16.png", filename: "favicon-16x16.png", notFound: constants.GET_SWAGGER_FAIL},
		{route: "/swagger/favicon-32x32.png", filename: "favicon-32x32.png", notFound: constants.GET_SWAGGER_FAIL},
	}

	for _, resource := range resources {
		item := resource
		server.AddRoute(rest.Route{
			Method: http.MethodGet,
			Path:   item.route,
			Handler: func(w http.ResponseWriter, r *http.Request) {
				serveEmbeddedDocs(w, item.filename, item.notFound)
			},
		})
	}
}

// serveEmbeddedDocs 从内嵌文件系统读取页面或静态资源并响应
// 读取失败时按 500 返回对应提示，避免把异常内容当成文档交给 Swagger UI
func serveEmbeddedDocs(w http.ResponseWriter, name, notFound string) {
	content, err := docs.StaticFiles.ReadFile(name)
	if err != nil {
		http.Error(w, notFound, http.StatusInternalServerError)
		return
	}
	if contentType, ok := swaggerContentTypes[path.Ext(name)]; ok {
		w.Header().Set("Content-Type", contentType)
	}
	w.WriteHeader(http.StatusOK)
	_, _ = w.Write(content)
}
