package redis

import (
	"context"
	"errors"
	"testing"
	"time"

	"app/common/cache"

	goredis "github.com/redis/go-redis/v9"
)

// cacheSetCall 记录一次 Set 调用的入参
type cacheSetCall struct {
	key   string
	value any
	ttl   time.Duration
}

// fakeCacheCommander 记录命令入参并返回预设结果的 Redis 命令替身，不建立真实连接
type fakeCacheCommander struct {
	getKeys   []string
	getResult *goredis.StringCmd
	setCalls  []cacheSetCall
	setResult *goredis.StatusCmd
	delCalls  [][]string
	delResult *goredis.IntCmd
}

// Get 记录 key 并返回预设结果
func (f *fakeCacheCommander) Get(_ context.Context, key string) *goredis.StringCmd {
	f.getKeys = append(f.getKeys, key)
	return f.getResult
}

// Set 记录入参并返回预设结果
func (f *fakeCacheCommander) Set(_ context.Context, key string, value any, expiration time.Duration) *goredis.StatusCmd {
	f.setCalls = append(f.setCalls, cacheSetCall{key: key, value: value, ttl: expiration})
	return f.setResult
}

// Del 记录 key 列表并返回预设结果
func (f *fakeCacheCommander) Del(_ context.Context, keys ...string) *goredis.IntCmd {
	f.delCalls = append(f.delCalls, keys)
	return f.delResult
}

// TestCacheStoreGetReturnsValue 命中时返回原始字节并透传 key
func TestCacheStoreGetReturnsValue(t *testing.T) {
	fake := &fakeCacheCommander{getResult: goredis.NewStringResult("payload", nil)}
	store := &CacheStore{client: fake}

	raw, err := store.Get(context.Background(), "cache:key")
	if err != nil {
		t.Fatalf("读取缓存失败: %v", err)
	}
	if string(raw) != "payload" {
		t.Fatalf("缓存内容 = %q，期望 payload", raw)
	}
	if len(fake.getKeys) != 1 || fake.getKeys[0] != "cache:key" {
		t.Fatalf("Get 调用入参 = %v", fake.getKeys)
	}
}

// TestCacheStoreGetMapsNilToErrCacheMiss key 不存在时统一返回 cache.ErrCacheMiss，供上层按未命中处理
func TestCacheStoreGetMapsNilToErrCacheMiss(t *testing.T) {
	fake := &fakeCacheCommander{getResult: goredis.NewStringResult("", goredis.Nil)}
	store := &CacheStore{client: fake}

	if _, err := store.Get(context.Background(), "cache:key"); !errors.Is(err, cache.ErrCacheMiss) {
		t.Fatalf("错误 = %v，期望 cache.ErrCacheMiss", err)
	}
}

// TestCacheStoreGetPassesOtherErrors 连接或命令错误必须原样上抛，不能被当成未命中吞掉
func TestCacheStoreGetPassesOtherErrors(t *testing.T) {
	cause := errors.New("redis 不可用")
	fake := &fakeCacheCommander{getResult: goredis.NewStringResult("", cause)}
	store := &CacheStore{client: fake}

	_, err := store.Get(context.Background(), "cache:key")
	if !errors.Is(err, cause) {
		t.Fatalf("错误 = %v，期望透传原始错误", err)
	}
	if errors.Is(err, cache.ErrCacheMiss) {
		t.Fatal("连接错误不应映射为 cache.ErrCacheMiss")
	}
}

// TestCacheStoreSetForwardsKeyValueTTL 写入时透传 key、值与过期时间
func TestCacheStoreSetForwardsKeyValueTTL(t *testing.T) {
	fake := &fakeCacheCommander{setResult: goredis.NewStatusResult("OK", nil)}
	store := &CacheStore{client: fake}

	if err := store.Set(context.Background(), "cache:key", []byte("value"), 90*time.Second); err != nil {
		t.Fatalf("写入缓存失败: %v", err)
	}
	if len(fake.setCalls) != 1 {
		t.Fatalf("Set 调用次数 = %d", len(fake.setCalls))
	}
	call := fake.setCalls[0]
	value, ok := call.value.([]byte)
	if !ok {
		t.Fatalf("Set 值类型 = %T，期望 []byte", call.value)
	}
	if call.key != "cache:key" || string(value) != "value" || call.ttl != 90*time.Second {
		t.Fatalf("Set 调用入参 = %+v", call)
	}
}

// TestCacheStoreSetReturnsError 写入失败必须返回错误供上层记录日志
func TestCacheStoreSetReturnsError(t *testing.T) {
	cause := errors.New("写入失败")
	fake := &fakeCacheCommander{setResult: goredis.NewStatusResult("", cause)}
	store := &CacheStore{client: fake}

	if err := store.Set(context.Background(), "cache:key", []byte("value"), time.Minute); !errors.Is(err, cause) {
		t.Fatalf("错误 = %v，期望透传原始错误", err)
	}
}

// TestCacheStoreDeleteSkipsEmptyKeys 空 key 列表不发起命令，直接视为成功
func TestCacheStoreDeleteSkipsEmptyKeys(t *testing.T) {
	fake := &fakeCacheCommander{}
	store := &CacheStore{client: fake}

	if err := store.Delete(context.Background()); err != nil {
		t.Fatalf("删除空 key 列表失败: %v", err)
	}
	if len(fake.delCalls) != 0 {
		t.Fatalf("空 key 列表不应发起 Del 调用: %v", fake.delCalls)
	}
}

// TestCacheStoreDeleteForwardsKeys 删除时一次提交全部 key
func TestCacheStoreDeleteForwardsKeys(t *testing.T) {
	fake := &fakeCacheCommander{delResult: goredis.NewIntResult(2, nil)}
	store := &CacheStore{client: fake}

	if err := store.Delete(context.Background(), "cache:a", "cache:b"); err != nil {
		t.Fatalf("删除缓存失败: %v", err)
	}
	if len(fake.delCalls) != 1 {
		t.Fatalf("Del 调用次数 = %d", len(fake.delCalls))
	}
	keys := fake.delCalls[0]
	if len(keys) != 2 || keys[0] != "cache:a" || keys[1] != "cache:b" {
		t.Fatalf("Del 调用入参 = %v", keys)
	}
}

// TestCacheStoreDeleteReturnsError 删除失败必须返回错误供上层记录日志
func TestCacheStoreDeleteReturnsError(t *testing.T) {
	cause := errors.New("删除失败")
	fake := &fakeCacheCommander{delResult: goredis.NewIntResult(0, cause)}
	store := &CacheStore{client: fake}

	if err := store.Delete(context.Background(), "cache:a"); !errors.Is(err, cause) {
		t.Fatalf("错误 = %v，期望透传原始错误", err)
	}
}

// TestNewCacheStoreReturnsNilWithoutClient 未配置 Redis 时返回 nil 接口，两级缓存据此退化为纯本地
func TestNewCacheStoreReturnsNilWithoutClient(t *testing.T) {
	if store := NewCacheStore(nil); store != nil {
		t.Fatalf("client 为 nil 时应返回 nil，实际 %#v", store)
	}
}
