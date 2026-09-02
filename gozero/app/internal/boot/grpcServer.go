package boot

import (
	"context"
	"errors"
	"net"
	"strconv"
	"strings"

	"app/common/constants"
	"app/common/keys"
	"app/common/utils"
	"app/internal/config"

	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/health"
	healthpb "google.golang.org/grpc/health/grpc_health_v1"
	"google.golang.org/grpc/metadata"
	"google.golang.org/grpc/status"
)

// GrpcServer 是与 REST 服务并行运行的 gRPC 基础设施服务。
// 业务 gRPC 服务在对应 proto 迁移时通过 proto 注册。
type GrpcServer struct {
	server *grpc.Server
	addr   string
}

// CreateGrpcServer 创建 gRPC 服务，并注册健康检查服务。
func CreateGrpcServer(c config.Config) *GrpcServer {
	if !c.Grpc.Enabled {
		return &GrpcServer{}
	}
	server := grpc.NewServer(grpc.ChainUnaryInterceptor(grpcContextInterceptor))
	healthpb.RegisterHealthServer(server, health.NewServer())
	return &GrpcServer{server: server, addr: ":" + strconv.Itoa(c.Grpc.Port)}
}

// Start 启动 gRPC 服务。该方法阻塞，应由启动流程放入 goroutine。
func (s *GrpcServer) Start() {
	if s.server == nil {
		return
	}
	listener, err := net.Listen("tcp", s.addr)
	if err != nil {
		panic(err)
	}
	if err = s.server.Serve(listener); err != nil && !errors.Is(err, grpc.ErrServerStopped) {
		panic(err)
	}
}

// Stop 优雅停止 gRPC 服务。
func (s *GrpcServer) Stop() {
	if s.server != nil {
		s.server.GracefulStop()
	}
}

func grpcContextInterceptor(
	ctx context.Context,
	request interface{},
	info *grpc.UnaryServerInfo,
	handler grpc.UnaryHandler,
) (interface{}, error) {
	if strings.HasPrefix(info.FullMethod, "/grpc.health.v1.Health/") {
		return handler(ctx, request)
	}
	metadataValue := func(name string) string {
		values := metadata.ValueFromIncomingContext(ctx, name)
		if len(values) == 0 {
			return ""
		}
		return values[0]
	}
	ctx = context.WithValue(ctx, keys.UserIDKey, parseUserID(metadataValue("x-user-id")))
	ctx = context.WithValue(ctx, keys.UsernameKey, metadataValue("x-username"))
	ctx = context.WithValue(ctx, keys.SessionIDKey, metadataValue("x-session-id"))
	ctx = context.WithValue(ctx, keys.TokenKey, bearerToken(metadataValue("authorization")))

	internalToken := bearerToken(metadataValue("x-internal-token"))
	if internalToken == "" {
		return nil, status.Error(codes.Unauthenticated, constants.INTERNAL_TOKEN_MISSING)
	}
	tokenUtil, err := utils.GetTokenUtil()
	if err != nil {
		return nil, status.Error(codes.Unauthenticated, constants.INTERNAL_TOKEN_NOT_INITIALIZED)
	}
	if _, err = tokenUtil.ValidateInternalToken(internalToken); err != nil {
		return nil, status.Error(codes.Unauthenticated, constants.INTERNAL_TOKEN_INVALID)
	}
	ctx = context.WithValue(ctx, keys.InternalTokenKey, internalToken)
	return handler(ctx, request)
}

func bearerToken(value string) string {
	return strings.TrimPrefix(value, "Bearer ")
}

func parseUserID(value string) int64 {
	if value == "" {
		return 0
	}
	userID, err := strconv.ParseInt(value, 10, 64)
	if err != nil {
		return 0
	}
	return userID
}
