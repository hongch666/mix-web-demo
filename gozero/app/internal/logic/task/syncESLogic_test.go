package task

import (
	"context"
	"errors"
	"testing"

	"app/common/constants"
	"app/common/utils"
	"app/internal/svc"
	"app/internal/types"
)

// syncESFuncFake 后台同步函数的替身，记录入参并通过 channel 通知调用完成
type syncESFuncFake struct {
	capturedContext context.Context
	capturedType    string
	capturedIDs     []int64
	returnErr       error
	called          chan struct{}
}

func newSyncESFuncFake(returnErr error) *syncESFuncFake {
	return &syncESFuncFake{returnErr: returnErr, called: make(chan struct{}, 1)}
}

func (f *syncESFuncFake) sync(ctx context.Context, _ *svc.ServiceContext, changeType string, ids []int64) error {
	f.capturedContext = ctx
	f.capturedType = changeType
	f.capturedIDs = ids
	f.called <- struct{}{}
	return f.returnErr
}

// newSyncESTestContext 构造仅包含同步任务所需依赖的服务上下文
func newSyncESTestContext(t *testing.T) *svc.ServiceContext {
	t.Helper()
	logger, err := utils.NewZeroLogger(t.TempDir())
	if err != nil {
		t.Fatalf("创建测试日志器失败: %v", err)
	}
	// t.Cleanup 按后进先出执行：先关日志再清理临时目录，
	// 否则 Windows 下日志文件句柄未释放会导致清理失败
	t.Cleanup(func() { _ = logger.Close() })
	return &svc.ServiceContext{
		RuntimeContext: &svc.RuntimeContext{Context: context.Background()},
		LoggerContext:  &svc.LoggerContext{Logger: logger},
	}
}

// stubSyncFunc 用替身替换后台同步函数并在测试结束后还原
func stubSyncFunc(t *testing.T, fake *syncESFuncFake) {
	t.Helper()
	original := syncArticleESChangesFunc
	syncArticleESChangesFunc = fake.sync
	t.Cleanup(func() { syncArticleESChangesFunc = original })
}

// stubSyncDispatchInline 将后台执行替换为同步执行，保证测试确定性
func stubSyncDispatchInline(t *testing.T) {
	t.Helper()
	original := runSyncInBackground
	runSyncInBackground = func(_ *SyncESLogic, task func()) { task() }
	t.Cleanup(func() { runSyncInBackground = original })
}

// 验证手动触发同步时后台任务收到拷贝后的请求字段并立即返回成功
func TestSyncESRunsBackgroundSyncWithCopiedRequestFields(t *testing.T) {
	fake := newSyncESFuncFake(nil)
	stubSyncFunc(t, fake)
	stubSyncDispatchInline(t)
	svcCtx := newSyncESTestContext(t)
	logic := NewSyncESLogic(context.Background(), svcCtx)
	t.Cleanup(func() { _ = logic.ZeroLogger.Close() })

	req := &types.SyncESReq{ChangeType: "update", Ids: []int64{7, 9}}
	resp, err := logic.SyncES(req)
	if err != nil || resp == nil {
		t.Fatalf("触发同步应立即返回成功: %+v, %v", resp, err)
	}

	// 返回后修改请求对象，验证后台任务拿到的是拷贝而非引用
	req.ChangeType = "delete"
	req.Ids[0] = 999

	<-fake.called
	if fake.capturedType != "update" || len(fake.capturedIDs) != 2 || fake.capturedIDs[0] != 7 || fake.capturedIDs[1] != 9 {
		t.Fatalf("后台同步参数不正确: type=%q ids=%v", fake.capturedType, fake.capturedIDs)
	}
	if fake.capturedContext != svcCtx.Context {
		t.Fatalf("后台同步应使用服务上下文的 Context: %v", fake.capturedContext)
	}
}

// 验证后台同步失败不影响触发接口的成功返回
func TestSyncESToleratesBackgroundSyncFailure(t *testing.T) {
	fake := newSyncESFuncFake(errors.New("sync failed"))
	stubSyncFunc(t, fake)
	stubSyncDispatchInline(t)
	svcCtx := newSyncESTestContext(t)
	logic := NewSyncESLogic(context.Background(), svcCtx)
	t.Cleanup(func() { _ = logic.ZeroLogger.Close() })

	resp, err := logic.SyncES(&types.SyncESReq{ChangeType: "delete", Ids: []int64{3}})
	if err != nil || resp == nil {
		t.Fatalf("后台失败不应影响触发返回: %+v, %v", resp, err)
	}

	<-fake.called
	if fake.capturedType != "delete" || len(fake.capturedIDs) != 1 || fake.capturedIDs[0] != 3 {
		t.Fatalf("后台同步参数不正确: type=%q ids=%v", fake.capturedType, fake.capturedIDs)
	}
}

// 验证触发接口在后台同步完成前就已返回
func TestSyncESReturnsBeforeBackgroundSyncCompletes(t *testing.T) {
	fake := newSyncESFuncFake(nil)
	stubSyncFunc(t, fake)
	svcCtx := newSyncESTestContext(t)
	logic := NewSyncESLogic(context.Background(), svcCtx)
	t.Cleanup(func() { _ = logic.ZeroLogger.Close() })

	// 用阻塞的同步函数配合真实的后台执行方式，验证接口先于后台任务返回
	// backgroundDone 在后台任务完全结束后关闭，保证测试清理不与日志写入竞态
	release := make(chan struct{})
	backgroundDone := make(chan struct{})
	originalDispatch := runSyncInBackground
	gatedSync := syncArticleESChangesFunc
	syncArticleESChangesFunc = func(ctx context.Context, ctxSvc *svc.ServiceContext, changeType string, ids []int64) error {
		<-release
		return gatedSync(ctx, ctxSvc, changeType, ids)
	}
	runSyncInBackground = func(l *SyncESLogic, task func()) {
		utils.SafeGo(l.ZeroLogger, constants.SAFE_GO_SYNC_ES_DATA, func() {
			task()
			close(backgroundDone)
		})
	}
	t.Cleanup(func() {
		syncArticleESChangesFunc = fake.sync
		runSyncInBackground = originalDispatch
	})

	resp, err := logic.SyncES(&types.SyncESReq{ChangeType: "insert", Ids: []int64{5}})
	if err != nil || resp == nil {
		t.Fatalf("触发同步应立即返回: %+v, %v", resp, err)
	}

	close(release)
	<-backgroundDone
}
