// Code scaffolded by goctl. Safe to edit.
// goctl {{.version}}

package {{.pkgName}}

import (
	"app/common/utils"
	{{.imports}}
)

type {{.logic}} struct {
	ctx    context.Context
	svcCtx *svc.ServiceContext
	*utils.ZeroLogger
}

// ZeroLogger 内部基于 logx 实现，而 goctl 会无条件注入 logx 导包，这里保留引用避免编译报导包未使用
var _ = logx.Logger{}

{{if .hasDoc}}{{.doc}}{{end}}
func New{{.logic}}(ctx context.Context, svcCtx *svc.ServiceContext) *{{.logic}} {
	return &{{.logic}}{
		ctx:        ctx,
		svcCtx:     svcCtx,
		ZeroLogger: svcCtx.Logger.WithContext(ctx),
	}
}

func (l *{{.logic}}) {{.function}}({{.request}}) {{.responseType}} {
	// todo: add your logic here and delete this line

	{{.returnString}}
}
