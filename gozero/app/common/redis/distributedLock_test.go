package redis

import (
	"context"
	"errors"
	"strings"
	"testing"
	"time"

	"app/common/constants"

	goredis "github.com/redis/go-redis/v9"
)

// lockSetCall 记录一次 SetNX 调用的入参
type lockSetCall struct {
	key   string
	value any
	ttl   time.Duration
}

// lockEvalCall 记录一次 Eval 调用的入参
type lockEvalCall struct {
	script string
	keys   []string
	args   []any
}

// fakeLockCommander 记录命令入参并返回预设结果的 Redis 命令替身，不建立真实连接
type fakeLockCommander struct {
	setCalls   []lockSetCall
	setResult  *goredis.BoolCmd
	evalCalls  []lockEvalCall
	evalResult *goredis.Cmd
}

// SetNX 记录入参并返回预设结果
func (f *fakeLockCommander) SetNX(_ context.Context, key string, value any, expiration time.Duration) *goredis.BoolCmd {
	f.setCalls = append(f.setCalls, lockSetCall{key: key, value: value, ttl: expiration})
	return f.setResult
}

// Eval 记录入参并返回预设结果
func (f *fakeLockCommander) Eval(_ context.Context, script string, keys []string, args ...any) *goredis.Cmd {
	f.evalCalls = append(f.evalCalls, lockEvalCall{script: script, keys: keys, args: args})
	return f.evalResult
}

// TestDistributedLockTryLockAcquires 加锁成功时返回锁标识并透传 key 与过期时间
func TestDistributedLockTryLockAcquires(t *testing.T) {
	fake := &fakeLockCommander{setResult: goredis.NewBoolResult(true, nil)}
	lock := &DistributedLock{client: fake}

	value, err := lock.TryLock(context.Background(), "lock:task", 30)
	if err != nil {
		t.Fatalf("加锁失败: %v", err)
	}
	if value == "" {
		t.Fatal("加锁成功应返回锁标识")
	}
	if len(fake.setCalls) != 1 {
		t.Fatalf("SetNX 调用次数 = %d", len(fake.setCalls))
	}
	call := fake.setCalls[0]
	if call.key != "lock:task" || call.ttl != 30*time.Second {
		t.Fatalf("SetNX 调用入参 = %+v", call)
	}
	if lockValue, ok := call.value.(string); !ok || lockValue != value {
		t.Fatalf("锁标识未写入 SetNX 值: %v", call.value)
	}
}

// TestDistributedLockTryLockReturnsEmptyWhenHeld 锁已被占用时返回空标识且不报错
func TestDistributedLockTryLockReturnsEmptyWhenHeld(t *testing.T) {
	fake := &fakeLockCommander{setResult: goredis.NewBoolResult(false, nil)}
	lock := &DistributedLock{client: fake}

	value, err := lock.TryLock(context.Background(), "lock:task", 30)
	if err != nil {
		t.Fatalf("锁被占用不应返回错误: %v", err)
	}
	if value != "" {
		t.Fatalf("锁被占用时标识应为空，实际 %q", value)
	}
}

// TestDistributedLockTryLockWrapsError 加锁命令异常必须包装为项目错误文案
func TestDistributedLockTryLockWrapsError(t *testing.T) {
	cause := errors.New("redis 不可用")
	fake := &fakeLockCommander{setResult: goredis.NewBoolResult(false, cause)}
	lock := &DistributedLock{client: fake}

	if _, err := lock.TryLock(context.Background(), "lock:task", 30); err == nil {
		t.Fatal("命令异常时应返回错误")
	} else if !strings.Contains(err.Error(), "获取分布式锁错误") {
		t.Fatalf("错误文案 = %q", err.Error())
	}
}

// TestDistributedLockUnlockReleases 解锁脚本返回 1 时视为释放成功，并透传 key 与锁标识
func TestDistributedLockUnlockReleases(t *testing.T) {
	fake := &fakeLockCommander{evalResult: goredis.NewCmdResult(int64(1), nil)}
	lock := &DistributedLock{client: fake}

	released, err := lock.Unlock(context.Background(), "lock:task", "lock-value")
	if err != nil {
		t.Fatalf("解锁失败: %v", err)
	}
	if !released {
		t.Fatal("脚本返回 1 应视为释放成功")
	}
	if len(fake.evalCalls) != 1 {
		t.Fatalf("Eval 调用次数 = %d", len(fake.evalCalls))
	}
	call := fake.evalCalls[0]
	if len(call.keys) != 1 || call.keys[0] != "lock:task" {
		t.Fatalf("Eval keys = %v", call.keys)
	}
	if len(call.args) != 1 || call.args[0] != "lock-value" {
		t.Fatalf("Eval 参数 = %v", call.args)
	}
	if call.script != constants.UNLOCK_LUA_SCRIPT {
		t.Fatalf("解锁脚本内容异常: %q", call.script)
	}
}

// TestDistributedLockUnlockKeepsLockForOtherOwner 脚本返回 0 表示锁已被他人持有，释放失败但不报错
func TestDistributedLockUnlockKeepsLockForOtherOwner(t *testing.T) {
	fake := &fakeLockCommander{evalResult: goredis.NewCmdResult(int64(0), nil)}
	lock := &DistributedLock{client: fake}

	released, err := lock.Unlock(context.Background(), "lock:task", "lock-value")
	if err != nil {
		t.Fatalf("释放失败不应返回错误: %v", err)
	}
	if released {
		t.Fatal("脚本返回 0 时不应视为释放成功")
	}
}

// TestDistributedLockUnlockWrapsError 解锁命令异常必须包装为项目错误文案
func TestDistributedLockUnlockWrapsError(t *testing.T) {
	cause := errors.New("redis 不可用")
	fake := &fakeLockCommander{evalResult: goredis.NewCmdResult(nil, cause)}
	lock := &DistributedLock{client: fake}

	if _, err := lock.Unlock(context.Background(), "lock:task", "lock-value"); err == nil {
		t.Fatal("命令异常时应返回错误")
	} else if !strings.Contains(err.Error(), "释放分布式锁错误") {
		t.Fatalf("错误文案 = %q", err.Error())
	}
}
