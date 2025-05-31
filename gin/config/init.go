package config

func Init() {
	// 初始化配置
	InitConfig()
	// 初始化Nacos
	InitNacos()
	// 初始化Gorm
	InitGorm()
}
