package cache

import (
	"context"
	"errors"
	"sync"
	"sync/atomic"
	"testing"
	"time"
)

// memoryStore 内存实现的 L2 存储，用于验证两级缓存的读写与失效行为
type memoryStore struct {
	mu     sync.Mutex
	data   map[string][]byte
	ttls   map[string]time.Duration
	getErr error
	setErr error
	delErr error
}

// newMemoryStore 创建空的内存存储
func newMemoryStore() *memoryStore {
	return &memoryStore{
		data: make(map[string][]byte),
		ttls: make(map[string]time.Duration),
	}
}

// Get 读取内存中的缓存副本，未命中返回 ErrCacheMiss
func (s *memoryStore) Get(_ context.Context, key string) ([]byte, error) {
	if s.getErr != nil {
		return nil, s.getErr
	}

	s.mu.Lock()
	defer s.mu.Unlock()

	raw, ok := s.data[key]
	if !ok {
		return nil, ErrCacheMiss
	}
	return raw, nil
}

// Set 写入内存缓存并记录过期时间
func (s *memoryStore) Set(_ context.Context, key string, value []byte, ttl time.Duration) error {
	if s.setErr != nil {
		return s.setErr
	}

	s.mu.Lock()
	defer s.mu.Unlock()

	s.data[key] = value
	s.ttls[key] = ttl
	return nil
}

// Delete 删除内存中的缓存 key
func (s *memoryStore) Delete(_ context.Context, keys ...string) error {
	if s.delErr != nil {
		return s.delErr
	}

	s.mu.Lock()
	defer s.mu.Unlock()

	for _, key := range keys {
		delete(s.data, key)
		delete(s.ttls, key)
	}
	return nil
}

// has 判断存储中是否存在指定 key
func (s *memoryStore) has(key string) bool {
	s.mu.Lock()
	defer s.mu.Unlock()

	_, ok := s.data[key]
	return ok
}

// TestMultiLevelCacheLocalHitSkipsLoader 本地缓存命中时不应回源
func TestMultiLevelCacheLocalHitSkipsLoader(t *testing.T) {
	ctx := context.Background()
	c := NewMultiLevelCache[string](Options{})
	c.Set(ctx, "key", "cached")

	loaderCalls := 0
	value, err := c.Get(ctx, "key", func(context.Context) (string, error) {
		loaderCalls++
		return "", errors.New("不应回源")
	})
	if err != nil {
		t.Fatalf("读取本地缓存失败: %v", err)
	}
	if value != "cached" {
		t.Fatalf("缓存值 = %q，期望 cached", value)
	}
	if loaderCalls != 0 {
		t.Fatalf("本地命中仍回源 %d 次", loaderCalls)
	}
}

// TestMultiLevelCacheStoreHitBackfillsLocal L2 命中后应回填本地，且不再回源
func TestMultiLevelCacheStoreHitBackfillsLocal(t *testing.T) {
	ctx := context.Background()
	store := newMemoryStore()
	writer := NewMultiLevelCache[string](Options{Store: store})
	writer.Set(ctx, "key", "from-store")

	reader := NewMultiLevelCache[string](Options{Store: store})
	loaderCalls := 0
	loader := func(context.Context) (string, error) {
		loaderCalls++
		return "", errors.New("不应回源")
	}

	value, err := reader.Get(ctx, "key", loader)
	if err != nil {
		t.Fatalf("读取 L2 缓存失败: %v", err)
	}
	if value != "from-store" {
		t.Fatalf("L2 返回值 = %q，期望 from-store", value)
	}
	if loaderCalls != 0 {
		t.Fatalf("L2 命中仍回源 %d 次", loaderCalls)
	}

	// 删除 L2 后再次读取仍应命中本地回填的副本
	if err := store.Delete(ctx, "key"); err != nil {
		t.Fatalf("删除 L2 缓存失败: %v", err)
	}
	if _, err := reader.Get(ctx, "key", loader); err != nil {
		t.Fatalf("本地回填后读取失败: %v", err)
	}
	if loaderCalls != 0 {
		t.Fatalf("本地回填后仍回源 %d 次", loaderCalls)
	}
}

// TestMultiLevelCacheConcurrentMissLoadsOnce 并发未命中时只回源一次
func TestMultiLevelCacheConcurrentMissLoadsOnce(t *testing.T) {
	ctx := context.Background()
	c := NewMultiLevelCache[int](Options{})

	var loaderCalls int64
	loader := func(context.Context) (int, error) {
		atomic.AddInt64(&loaderCalls, 1)
		time.Sleep(10 * time.Millisecond)
		return 42, nil
	}

	const workers = 8
	var wg sync.WaitGroup
	results := make([]int, workers)
	errs := make([]error, workers)
	for i := 0; i < workers; i++ {
		wg.Add(1)
		go func(index int) {
			defer wg.Done()
			results[index], errs[index] = c.Get(ctx, "key", loader)
		}(i)
	}
	wg.Wait()

	if calls := atomic.LoadInt64(&loaderCalls); calls != 1 {
		t.Fatalf("回源次数 = %d，期望 1", calls)
	}
	for i := 0; i < workers; i++ {
		if errs[i] != nil {
			t.Fatalf("第 %d 个请求失败: %v", i, errs[i])
		}
		if results[i] != 42 {
			t.Fatalf("第 %d 个请求返回值 = %d，期望 42", i, results[i])
		}
	}
}

// TestMultiLevelCacheFallsBackToStaleOnLoaderError 本地过期且回源失败时降级返回旧值
func TestMultiLevelCacheFallsBackToStaleOnLoaderError(t *testing.T) {
	ctx := context.Background()
	store := newMemoryStore()
	c := NewMultiLevelCache[string](Options{Store: store})
	c.Set(ctx, "key", "stale-value")

	// 本地条目改为已过期，同时清空 L2，强制走回源
	c.mu.Lock()
	c.entries["key"].expiresAt = time.Now().Add(-time.Second)
	c.mu.Unlock()
	if err := store.Delete(ctx, "key"); err != nil {
		t.Fatalf("删除 L2 缓存失败: %v", err)
	}

	value, err := c.Get(ctx, "key", func(context.Context) (string, error) {
		return "", errors.New("fastapi 不可用")
	})
	if err != nil {
		t.Fatalf("降级应该成功: %v", err)
	}
	if value != "stale-value" {
		t.Fatalf("降级返回值 = %q，期望 stale-value", value)
	}
}

// TestMultiLevelCacheReturnsLoaderErrorWithoutStale 没有任何旧值时回源错误必须向上返回
func TestMultiLevelCacheReturnsLoaderErrorWithoutStale(t *testing.T) {
	ctx := context.Background()
	c := NewMultiLevelCache[string](Options{})

	_, err := c.Get(ctx, "missing", func(context.Context) (string, error) {
		return "", errors.New("fastapi 不可用")
	})
	if err == nil {
		t.Fatal("缺少旧值时应返回回源错误")
	}
}

// TestMultiLevelCacheDegradesWhenStoreMissing 未配置 L2 时退化为纯本地缓存
func TestMultiLevelCacheDegradesWhenStoreMissing(t *testing.T) {
	ctx := context.Background()
	c := NewMultiLevelCache[string](Options{})

	value, err := c.Get(ctx, "key", func(context.Context) (string, error) {
		return "loaded", nil
	})
	if err != nil {
		t.Fatalf("回源失败: %v", err)
	}
	if value != "loaded" {
		t.Fatalf("返回值 = %q，期望 loaded", value)
	}

	c.Delete(ctx, "key")
	if _, ok := c.getLocal("key"); ok {
		t.Fatal("Delete 后本地缓存应被清除")
	}
}

// TestMultiLevelCacheStoreErrorFallsThroughToLoader L2 读取异常时按未命中处理并继续回源
func TestMultiLevelCacheStoreErrorFallsThroughToLoader(t *testing.T) {
	ctx := context.Background()
	store := newMemoryStore()
	store.getErr = errors.New("redis 不可用")
	c := NewMultiLevelCache[string](Options{Store: store})

	value, err := c.Get(ctx, "key", func(context.Context) (string, error) {
		return "loaded", nil
	})
	if err != nil {
		t.Fatalf("L2 异常时应回源成功: %v", err)
	}
	if value != "loaded" {
		t.Fatalf("返回值 = %q，期望 loaded", value)
	}
}

// TestMultiLevelCacheDeleteRemovesBothLevels 删除应同时清理本地与 L2
func TestMultiLevelCacheDeleteRemovesBothLevels(t *testing.T) {
	ctx := context.Background()
	store := newMemoryStore()
	c := NewMultiLevelCache[string](Options{KeyPrefix: "prefix:", Store: store})
	c.Set(ctx, "key", "cached")

	if !store.has("prefix:key") {
		t.Fatal("L2 应按前缀写入缓存 key")
	}

	c.Delete(ctx, "key")
	if _, ok := c.getLocal("key"); ok {
		t.Fatal("Delete 后本地缓存应被清除")
	}
	if store.has("prefix:key") {
		t.Fatal("Delete 后 L2 缓存应被清除")
	}
}

// TestMultiLevelCacheEvictsOldestEntry 本地条目超过上限时淘汰最早写入的条目
func TestMultiLevelCacheEvictsOldestEntry(t *testing.T) {
	ctx := context.Background()
	c := NewMultiLevelCache[int](Options{LocalMaxEntries: 2})

	c.Set(ctx, "first", 1)
	c.Set(ctx, "second", 2)
	c.Set(ctx, "third", 3)

	if _, ok := c.getLocal("first"); ok {
		t.Fatal("超出容量后最早写入的条目应被淘汰")
	}
	if _, ok := c.getLocal("third"); !ok {
		t.Fatal("最新写入的条目应保留")
	}
}
