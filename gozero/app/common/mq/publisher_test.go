package mq

import (
	"encoding/json"
	"errors"
	"strings"
	"sync"
	"testing"

	"app/common/constants"

	rabbitmq "github.com/wagslane/go-rabbitmq"
)

// publishCall 记录一次 Publish 调用的入参
type publishCall struct {
	data        []byte
	routingKeys []string
}

// fakePublisher 记录命令入参并返回预设结果的发布器替身，不建立真实连接
type fakePublisher struct {
	mu        sync.Mutex
	calls     []publishCall
	result    error
	closeFlag bool
}

// Publish 记录入参并返回预设结果
func (f *fakePublisher) Publish(data []byte, routingKeys []string, _ ...func(*rabbitmq.PublishOptions)) error {
	f.mu.Lock()
	defer f.mu.Unlock()
	f.calls = append(f.calls, publishCall{data: data, routingKeys: routingKeys})
	return f.result
}

// Close 标记发布通道已关闭
func (f *fakePublisher) Close() {
	f.mu.Lock()
	defer f.mu.Unlock()
	f.closeFlag = true
}

// isClosed 返回发布通道是否已关闭
func (f *fakePublisher) isClosed() bool {
	f.mu.Lock()
	defer f.mu.Unlock()
	return f.closeFlag
}

// TestPublishJSONDeliversQueueAndPayload 投递时以队列为 routingKey 并序列化 payload
func TestPublishJSONDeliversQueueAndPayload(t *testing.T) {
	fake := &fakePublisher{}
	publisher := &Publisher{publisher: fake}

	if err := publisher.PublishJSON(constants.API_LOG_QUEUE, map[string]any{"keyword": "redis"}); err != nil {
		t.Fatalf("投递失败: %v", err)
	}
	if len(fake.calls) != 1 {
		t.Fatalf("Publish 调用次数 = %d", len(fake.calls))
	}

	call := fake.calls[0]
	if len(call.routingKeys) != 1 || call.routingKeys[0] != constants.API_LOG_QUEUE {
		t.Fatalf("routingKeys = %v", call.routingKeys)
	}

	var payload map[string]any
	if err := json.Unmarshal(call.data, &payload); err != nil {
		t.Fatalf("投递内容不是合法 JSON: %v", err)
	}
	if payload["keyword"] != "redis" {
		t.Fatalf("投递内容 = %v", payload)
	}
}

// TestPublishJSONOnNilReceiverReturnsError nil 接收方投递时必须返回错误，由调用方记录日志
func TestPublishJSONOnNilReceiverReturnsError(t *testing.T) {
	var publisher *Publisher
	err := publisher.PublishJSON(constants.API_LOG_QUEUE, map[string]any{})
	if err == nil || !strings.Contains(err.Error(), constants.MQ_PUBLISHER_NOT_INITIALIZED_ERROR) {
		t.Fatalf("错误 = %v，期望包含未初始化文案", err)
	}
}

// TestPublishJSONWithoutCommanderReturnsError 未装配底层发布器时投递必须返回错误
func TestPublishJSONWithoutCommanderReturnsError(t *testing.T) {
	publisher := &Publisher{}

	if err := publisher.PublishJSON(constants.API_LOG_QUEUE, map[string]any{}); err == nil ||
		!strings.Contains(err.Error(), constants.MQ_PUBLISHER_NOT_INITIALIZED_ERROR) {
		t.Fatalf("错误 = %v，期望包含未初始化文案", err)
	}
}

// TestPublishJSONWrapsMarshalFailure payload 无法序列化时返回序列化错误
func TestPublishJSONWrapsMarshalFailure(t *testing.T) {
	fake := &fakePublisher{}
	publisher := &Publisher{publisher: fake}

	err := publisher.PublishJSON(constants.API_LOG_QUEUE, map[string]any{"ch": make(chan int)})
	if err == nil || !strings.Contains(err.Error(), "序列化 MQ 消息失败") {
		t.Fatalf("错误 = %v，期望序列化失败文案", err)
	}
	if len(fake.calls) != 0 {
		t.Fatalf("序列化失败不应发起 Publish 调用")
	}
}

// TestPublishJSONPassesUnderlyingError 底层投递错误必须原样上抛供调用方记录
func TestPublishJSONPassesUnderlyingError(t *testing.T) {
	cause := errors.New("amqp 不可用")
	fake := &fakePublisher{result: cause}
	publisher := &Publisher{publisher: fake}

	if err := publisher.PublishJSON(constants.API_LOG_QUEUE, map[string]any{}); !errors.Is(err, cause) {
		t.Fatalf("错误 = %v，期望透传原始错误", err)
	}
}

// TestNewPublisherRejectsEmptyURL 空连接地址必须直接报错，避免建立无效连接
func TestNewPublisherRejectsEmptyURL(t *testing.T) {
	if _, err := NewPublisher(""); err == nil || !strings.Contains(err.Error(), constants.MQ_AMQP_URL_EMPTY_ERROR) {
		t.Fatalf("错误 = %v，期望连接地址为空文案", err)
	}
}

// TestCloseReleasesChannelAndIsIdempotent Close 应关闭发布通道且重复调用安全
func TestCloseReleasesChannelAndIsIdempotent(t *testing.T) {
	fake := &fakePublisher{}
	publisher := &Publisher{publisher: fake}

	publisher.Close()
	publisher.Close()
	if !fake.isClosed() {
		t.Fatal("Close 后应关闭发布通道")
	}
}
