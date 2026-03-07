package boot

import (
	"app/common/utils"
	"net/http"

	swaggerFiles "github.com/swaggo/files"
	"github.com/swaggo/swag"
	"github.com/zeromicro/go-zero/rest"
)

// registerSwaggerRoute 注册 Swagger 文档路由
func registerSwaggerRoute(server *rest.Server) {
	// /swagger 重定向到 /swagger/index.html
	server.AddRoute(rest.Route{
		Method: http.MethodGet,
		Path:   "/swagger",
		Handler: func(w http.ResponseWriter, r *http.Request) {
			http.Redirect(w, r, "/swagger/index.html", http.StatusMovedPermanently)
		},
	})

	// /swagger/index.html 返回自定义 HTML，引用本地静态资源
	server.AddRoute(rest.Route{
		Method: http.MethodGet,
		Path:   "/swagger/index.html",
		Handler: func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Content-Type", "text/html; charset=utf-8")
			w.WriteHeader(http.StatusOK)
			_, _ = w.Write([]byte(utils.SWAGGER_HTML))
		},
	})

	// /swagger/doc.json 直接从内存中返回 Swagger JSON 数据
	server.AddRoute(rest.Route{
		Method: http.MethodGet,
		Path:   "/swagger/doc.json",
		Handler: func(w http.ResponseWriter, r *http.Request) {
			doc, err := swag.ReadDoc()
			if err != nil {
				http.Error(w, utils.GET_SWAGGER_FAIL, http.StatusInternalServerError)
				return
			}
			w.Header().Set("Content-Type", "application/json; charset=utf-8")
			w.WriteHeader(http.StatusOK)
			_, _ = w.Write([]byte(doc))
		},
	})

	// swagger-ui 静态文件：从 swaggo/files 内嵌的文件系统中读取，无需外网
	staticFiles := []string{
		"swagger-ui.css",
		"swagger-ui-bundle.js",
		"swagger-ui-standalone-preset.js",
		"swagger-ui-standalone-preset.js.map",
		"swagger-ui-bundle.js.map",
		"favicon-16x16.png",
		"favicon-32x32.png",
	}

	for _, filename := range staticFiles {
		fn := filename
		server.AddRoute(rest.Route{
			Method: http.MethodGet,
			Path:   "/swagger/" + fn,
			Handler: func(w http.ResponseWriter, r *http.Request) {
				serveEmbeddedFile(w, r, fn)
			},
		})
	}
}

// serveEmbeddedFile 将请求路径映射为 swaggo/files 内嵌文件系统中的路径，离线响应静态资源
func serveEmbeddedFile(w http.ResponseWriter, r *http.Request, filename string) {
	// 克隆请求副本，避免修改原始请求影响其他中间件
	r2 := r.Clone(r.Context())
	r2.URL.Path = "/" + filename
	swaggerFiles.Handler.ServeHTTP(w, r2)
}
