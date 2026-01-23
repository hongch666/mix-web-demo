package config

import (
	"log"
	"os"

	"github.com/nacos-group/nacos-sdk-go/v2/clients"
	"github.com/nacos-group/nacos-sdk-go/v2/clients/naming_client"
	"github.com/nacos-group/nacos-sdk-go/v2/common/constant"
	"github.com/nacos-group/nacos-sdk-go/v2/vo"
)

var NamingClient naming_client.INamingClient

func InitNacos() {
	// 创建缓存和日志目录（如果不存在）
	if err := os.MkdirAll(Config.Nacos.CacheDir, 0755); err != nil {
		log.Fatalf(CREATE_CACHE_DIR_FAILURE_MESSAGE, err)
	}
	if err := os.MkdirAll(Config.Nacos.LogDir, 0755); err != nil {
		log.Fatalf(CREATE_LOG_DIR_FAILURE_MESSAGE, err)
	}

	// 配置 Nacos 服务地址
	serverConfigs := []constant.ServerConfig{
		{
			IpAddr: Config.Nacos.IpAddr, // Nacos 服务器 IP
			Port:   uint64(Config.Nacos.Port),
		},
	}

	// 配置客户端参数
	clientConfig := constant.ClientConfig{
		NamespaceId:         Config.Nacos.Namespace, // public空间
		TimeoutMs:           5000,
		NotLoadCacheAtStart: true,
		LogLevel:            "error",
		CacheDir:            Config.Nacos.CacheDir, // 从配置文件读取
		LogDir:              Config.Nacos.LogDir,   // 从配置文件读取
	}

	// 创建 NamingClient
	var err error
	NamingClient, err = clients.NewNamingClient(vo.NacosClientParam{
		ClientConfig:  &clientConfig,
		ServerConfigs: serverConfigs,
	})
	if err != nil {
		log.Fatalf(CREATE_NACOS_NAMING_CLIENT_FAILURE_MESSAGE, err)
	}

	// 注册服务实例
	success, err := NamingClient.RegisterInstance(vo.RegisterInstanceParam{
		Ip:          Config.Server.Ip,           // 服务IP
		Port:        uint64(Config.Server.Port), // 服务端口
		ServiceName: Config.Nacos.ServiceName,
		GroupName:   Config.Nacos.GroupName,
		ClusterName: Config.Nacos.ClusterName,
		Weight:      1.0,
		Enable:      true,
		Healthy:     true,
		Ephemeral:   true,
	})
	if err != nil || !success {
		log.Fatalf(SERVICE_REGISTRATION_FAILURE_MESSAGE, err)
	}

	log.Println(SERVICE_REGISTRATION_SUCCESS_MESSAGE)
}
