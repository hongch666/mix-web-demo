package types

// Validate 校验同步任务请求参数
// SyncESReq 为空请求体，没有字段需要校验
// 保留此方法是为了满足 handler 模板对请求类型的要求：模板会为任何带请求类型的路由生成
// req.Validate() 调用，缺少该方法会导致重新生成的 handler 无法编译
func (r *SyncESReq) Validate() error {
	return nil
}
