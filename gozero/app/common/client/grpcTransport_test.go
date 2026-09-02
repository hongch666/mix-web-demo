package client

import (
	"context"
	"encoding/json"
	"errors"
	"net"
	"strconv"
	"syscall"
	"testing"
	"time"

	"app/common/utils"
	commonv1 "app/proto/commonv1"
	fastapiv1 "app/proto/fastapiv1"
	"github.com/nacos-group/nacos-sdk-go/v2/model"
	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
)

type grpcTransportTestServer struct {
	fastapiv1.UnimplementedSearchEnhanceServer
	fastapiv1.UnimplementedAlgorithmServer
}

func (s *grpcTransportTestServer) EnhanceGraph(context.Context, *fastapiv1.GraphEnhanceRequest) (*resultMessage, error) {
	return resultMessageWithData(map[string]any{"channel": "grpc", "method": "graph"}), nil
}

func (s *grpcTransportTestServer) EnhanceVector(context.Context, *fastapiv1.VectorEnhanceRequest) (*resultMessage, error) {
	return resultMessageWithData(map[string]any{"channel": "grpc", "method": "vector"}), nil
}

func (s *grpcTransportTestServer) GetSearchWeights(context.Context, *fastapiv1.EmptyRequest) (*resultMessage, error) {
	return resultMessageWithData(map[string]any{"channel": "grpc", "method": "weights"}), nil
}

// resultMessage 是测试服务返回的最小 common.v1.Result 实现别名。
type resultMessage = commonv1.Result

func resultMessageWithData(data map[string]any) *resultMessage {
	payload, _ := json.Marshal(data)
	return &resultMessage{Code: 200, Message: "success", Data: payload}
}

func TestGrpcTransportInvokePilotEndpoints(t *testing.T) {
	if err := utils.InitInternalTokenUtil("grpc-test-secret", time.Minute.Milliseconds()); err != nil {
		t.Fatal(err)
	}
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		if errors.Is(err, syscall.EPERM) {
			t.Skipf("当前执行环境禁止监听本地端口: %v", err)
		}
		t.Fatal(err)
	}
	server := grpc.NewServer()
	fastapiv1.RegisterSearchEnhanceServer(server, &grpcTransportTestServer{})
	fastapiv1.RegisterAlgorithmServer(server, &grpcTransportTestServer{})
	go server.Serve(listener)
	defer server.Stop()

	transport := newGrpcTransport()
	instance := &model.Instance{
		Ip: listener.Addr().(*net.TCPAddr).IP.String(),
		Metadata: map[string]string{
			"grpc_port": strconv.Itoa(listener.Addr().(*net.TCPAddr).Port),
		},
	}
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()

	paths := []string{"/graph-search/enhance", "/vector-search/enhance", "/algorithm/search/weights"}
	for _, path := range paths {
		result, callErr := transport.invoke(ctx, instance, path, RequestOptions{
			BodyData: map[string]any{
				"user_id": int64(101), "keyword": "grpc", "article_ids": []int64{1},
				"tags": []string{"test"}, "limit": int64(10), "top_k": int64(5),
			},
		})
		if callErr != nil {
			t.Fatalf("path %s invoke failed: %v", path, callErr)
		}
		if result.Code != 200 || result.Data == nil {
			t.Fatalf("path %s returned invalid result: %+v", path, result)
		}
	}
}

func TestGrpcTransportClassifiesBusinessErrorWithoutFallback(t *testing.T) {
	err := status.Error(codes.InvalidArgument, "invalid request")
	if isGrpcChannelError(err) {
		t.Fatal("business error must not be classified as channel error")
	}
}
