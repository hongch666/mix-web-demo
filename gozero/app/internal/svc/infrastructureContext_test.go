package svc

import (
	"errors"
	"os"
	"path/filepath"
	"testing"
	"time"

	"app/common/constants"
	"app/common/utils"
	"app/internal/config"

	"github.com/nacos-group/nacos-sdk-go/v2/vo"
	"github.com/zeromicro/go-zero/rest"
)

// fakeNacosRegistrar 记录注册调用次数与参数，按预设错误序列返回结果
type fakeNacosRegistrar struct {
	errs     []error
	attempts int
	last     vo.RegisterInstanceParam
}

// RegisterInstance 按调用次序返回预设错误，序列用尽后返回成功
func (f *fakeNacosRegistrar) RegisterInstance(param vo.RegisterInstanceParam) (bool, error) {
	f.attempts++
	f.last = param
	if f.attempts <= len(f.errs) {
		return false, f.errs[f.attempts-1]
	}
	return true, nil
}

// newTestLogger 创建写入临时目录的日志实例，测试结束关闭句柄
func newTestLogger(t *testing.T) *utils.ZeroLogger {
	t.Helper()

	logger, err := utils.NewZeroLogger(t.TempDir())
	if err != nil {
		t.Fatalf("创建测试日志实例失败: %v", err)
	}
	t.Cleanup(func() {
		if err := logger.Close(); err != nil {
			t.Logf("关闭测试日志实例失败: %v", err)
		}
	})

	return logger
}

// stubDetectLocalIP 固定本机 IP 探测结果，避免测试依赖真实网卡
func stubDetectLocalIP(t *testing.T, ip string) {
	t.Helper()

	original := detectLocalIP
	detectLocalIP = func() (string, error) { return ip, nil }
	t.Cleanup(func() { detectLocalIP = original })
}

// stubNacosRetrySleep 记录重试等待次数并跳过真实等待
func stubNacosRetrySleep(t *testing.T) *int {
	t.Helper()

	sleeps := 0
	original := sleepBeforeNacosRetry
	sleepBeforeNacosRetry = func(time.Duration) { sleeps++ }
	t.Cleanup(func() { sleepBeforeNacosRetry = original })

	return &sleeps
}

// stubNacosBackgroundRunner 把后台补注册改为同步执行，避免测试与 goroutine 并发读写
func stubNacosBackgroundRunner(t *testing.T) {
	t.Helper()

	original := nacosBackgroundRunner
	nacosBackgroundRunner = func(_ *utils.ZeroLogger, _ string, task func()) { task() }
	t.Cleanup(func() { nacosBackgroundRunner = original })
}

// newRegisterTestConfig 构造注册逻辑所需的最小配置
func newRegisterTestConfig() config.Config {
	return config.Config{
		RestConf: rest.RestConf{Host: "0.0.0.0", Port: 8082},
		Nacos: config.NacosConfig{
			IpAddr:      "127.0.0.1",
			Port:        8848,
			ServiceName: "gozero",
			GroupName:   "DEFAULT_GROUP",
			ClusterName: "DEFAULT",
		},
	}
}

// TestResolveNacosWritableDirKeepsConfiguredPath 配置目录可写时直接使用配置路径
func TestResolveNacosWritableDirKeepsConfiguredPath(t *testing.T) {
	configured := filepath.Join(t.TempDir(), "nacos", constants.NacosLogDirName)

	got := resolveNacosWritableDir(constants.NacosLogDirName, configured, newTestLogger(t))

	if got != configured {
		t.Fatalf("应返回配置路径 %s，实际 %s", configured, got)
	}
	if info, err := os.Stat(got); err != nil || !info.IsDir() {
		t.Fatalf("配置路径应已被创建为目录: err=%v", err)
	}
}

// TestResolveNacosWritableDirFallsBackWhenConfiguredPathUnusable 配置目录无法创建时回退到系统临时目录
func TestResolveNacosWritableDirFallsBackWhenConfiguredPathUnusable(t *testing.T) {
	blocker := filepath.Join(t.TempDir(), "blocker")
	if err := os.WriteFile(blocker, []byte("x"), 0o600); err != nil {
		t.Fatalf("准备阻塞文件失败: %v", err)
	}
	configured := filepath.Join(blocker, constants.NacosCacheDirName)
	expected := filepath.Join(os.TempDir(), constants.NacosTempDirName, constants.NacosCacheDirName)

	got := resolveNacosWritableDir(constants.NacosCacheDirName, configured, newTestLogger(t))

	if got != expected {
		t.Fatalf("应回退到 %s，实际 %s", expected, got)
	}
	if info, err := os.Stat(got); err != nil || !info.IsDir() {
		t.Fatalf("回退目录应已被创建: err=%v", err)
	}
}

// TestResolveNacosWritableDirUsesFallbackWhenPathEmpty 未配置目录时直接使用系统临时目录
func TestResolveNacosWritableDirUsesFallbackWhenPathEmpty(t *testing.T) {
	expected := filepath.Join(os.TempDir(), constants.NacosTempDirName, constants.NacosLogDirName)

	got := resolveNacosWritableDir(constants.NacosLogDirName, "", newTestLogger(t))

	if got != expected {
		t.Fatalf("应返回 %s，实际 %s", expected, got)
	}
}

// TestRegisterNacosInstanceRetriesThenDegrades 注册持续失败时先启动阶段重试再后台补注册，全程不 panic
func TestRegisterNacosInstanceRetriesThenDegrades(t *testing.T) {
	stubDetectLocalIP(t, "172.18.0.18")
	stubNacosBackgroundRunner(t)
	sleeps := stubNacosRetrySleep(t)
	totalAttempts := constants.NacosRegisterRetries + constants.NacosRegisterBackgroundRetries
	registrar := &fakeNacosRegistrar{errs: make([]error, totalAttempts)}
	for i := range registrar.errs {
		registrar.errs[i] = errors.New("client not connected")
	}

	registerNacosInstance(registrar, newRegisterTestConfig(), newTestLogger(t))

	if registrar.attempts != totalAttempts {
		t.Fatalf("应尝试 %d 次，实际 %d 次", totalAttempts, registrar.attempts)
	}
	if *sleeps != totalAttempts-2 {
		t.Fatalf("应等待 %d 次，实际 %d 次", totalAttempts-2, *sleeps)
	}
	if registrar.last.Ip != "172.18.0.18" || registrar.last.Port != 8082 || registrar.last.ServiceName != "gozero" {
		t.Fatalf("注册参数不符合配置: %+v", registrar.last)
	}
}

// TestRegisterNacosInstanceSucceedsInBackground 启动阶段失败后由后台补注册成功
func TestRegisterNacosInstanceSucceedsInBackground(t *testing.T) {
	stubDetectLocalIP(t, "172.18.0.18")
	stubNacosBackgroundRunner(t)
	stubNacosRetrySleep(t)
	registrar := &fakeNacosRegistrar{errs: make([]error, constants.NacosRegisterRetries+2)}
	for i := range registrar.errs {
		registrar.errs[i] = errors.New("client not connected")
	}

	registerNacosInstance(registrar, newRegisterTestConfig(), newTestLogger(t))

	expected := constants.NacosRegisterRetries + 3
	if registrar.attempts != expected {
		t.Fatalf("后台补注册成功后应停止，期望 %d 次，实际 %d 次", expected, registrar.attempts)
	}
}

// TestRegisterNacosInstanceStopsAfterSuccess 注册成功后立即返回，不再重试
func TestRegisterNacosInstanceStopsAfterSuccess(t *testing.T) {
	stubDetectLocalIP(t, "172.18.0.18")
	sleeps := stubNacosRetrySleep(t)
	registrar := &fakeNacosRegistrar{errs: []error{errors.New("client not connected")}}

	registerNacosInstance(registrar, newRegisterTestConfig(), newTestLogger(t))

	if registrar.attempts != 2 {
		t.Fatalf("应在第 2 次成功后停止，实际调用 %d 次", registrar.attempts)
	}
	if *sleeps != 1 {
		t.Fatalf("两次尝试之间应等待 1 次，实际 %d 次", *sleeps)
	}
}

// TestRegisterNacosInstanceSkipsWithoutServiceName 缺少服务名时不发起注册
func TestRegisterNacosInstanceSkipsWithoutServiceName(t *testing.T) {
	stubDetectLocalIP(t, "172.18.0.18")
	stubNacosRetrySleep(t)
	cfg := newRegisterTestConfig()
	cfg.Nacos.ServiceName = ""
	registrar := &fakeNacosRegistrar{}

	registerNacosInstance(registrar, cfg, newTestLogger(t))

	if registrar.attempts != 0 {
		t.Fatalf("缺少服务名时不应注册，实际调用 %d 次", registrar.attempts)
	}
}
