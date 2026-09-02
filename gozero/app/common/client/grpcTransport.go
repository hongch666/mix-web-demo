package client

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"net"
	"strconv"
	"sync"

	"app/common/constants"
	"app/common/keys"
	"app/common/utils"
	commonv1 "app/proto/commonv1"
	fastapiv1 "app/proto/fastapiv1"
	nestjsv1 "app/proto/nestjsv1"
	springv1 "app/proto/springv1"

	"github.com/nacos-group/nacos-sdk-go/v2/model"
	"github.com/zeromicro/go-zero/core/logx"
	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/grpc/metadata"
	"google.golang.org/grpc/status"
)

type grpcTransport struct {
	connections sync.Map
}

func newGrpcTransport() *grpcTransport {
	return &grpcTransport{}
}

func (t *grpcTransport) supports(path string) bool {
	return path == "/graph-search/enhance" ||
		path == "/vector-search/enhance" ||
		path == "/algorithm/search/weights" ||
		path == "/algorithm/search/script" ||
		path == "/algorithm/search/script-params" ||
		path == "/ai_history/internal/:id" ||
		path == "/article-logs/search-history/:user_id" ||
		path == "/articles/list" ||
		path == "/articles/batch" ||
		path == "/articles/views/batch" ||
		path == "/category/batch" ||
		path == "/category/sub/batch" ||
		path == "/users/:id" || path == "/users/batch" || path == "/users/by-name" ||
		path == "/users/by-github-id/:githubId" || path == "/users/github-user" ||
		path == "/users/:id/is-admin" || path == "/users/github/token-ticket" ||
		path == "/comments/scores/batch" || path == "/likes/counts/batch" ||
		path == "/collects/counts/batch" || path == "/focus/counts/batch"
}

func (t *grpcTransport) invoke(ctx context.Context, instance *model.Instance, path string, opts RequestOptions) (Result, error) {
	if instance == nil || instance.Metadata["grpc_port"] == "" {
		return Result{}, errGrpcUnavailable
	}
	port, err := strconv.Atoi(instance.Metadata["grpc_port"])
	if err != nil || port <= 0 {
		return Result{}, errGrpcUnavailable
	}
	address := net.JoinHostPort(instance.Ip, strconv.Itoa(port))
	connection, err := t.connection(ctx, address)
	if err != nil {
		return Result{}, err
	}

	requestMetadata := metadata.Pairs(
		"x-user-id", strconv.FormatInt(contextInt64(ctx, keys.UserIDKey), 10),
		"x-username", contextString(ctx, keys.UsernameKey),
		"x-session-id", contextString(ctx, keys.SessionIDKey),
	)
	if token := contextString(ctx, keys.TokenKey); token != "" {
		requestMetadata.Append("authorization", "Bearer "+token)
	}
	if tokenUtil, tokenErr := utils.GetTokenUtil(); tokenErr == nil {
		userID := contextInt64(ctx, keys.UserIDKey)
		if userID <= 0 {
			userID = -1
		}
		if token, tokenErr := tokenUtil.GenerateInternalToken(userID, "gozero"); tokenErr == nil {
			requestMetadata.Append("x-internal-token", "Bearer "+token)
		}
	}
	callCtx := metadata.NewOutgoingContext(ctx, requestMetadata)

	switch path {
	case "/graph-search/enhance":
		response, callErr := fastapiv1.NewSearchEnhanceClient(connection).EnhanceGraph(callCtx, buildGraphRequest(opts.BodyData))
		return resultFromGrpc(response, callErr)
	case "/vector-search/enhance":
		response, callErr := fastapiv1.NewSearchEnhanceClient(connection).EnhanceVector(callCtx, buildVectorRequest(opts.BodyData))
		return resultFromGrpc(response, callErr)
	case "/algorithm/search/weights":
		response, callErr := fastapiv1.NewAlgorithmClient(connection).GetSearchWeights(callCtx, &fastapiv1.EmptyRequest{})
		return resultFromGrpc(response, callErr)
	case "/algorithm/search/script":
		response, callErr := fastapiv1.NewAlgorithmClient(connection).GetSearchScript(callCtx, &fastapiv1.EmptyRequest{})
		return resultFromGrpc(response, callErr)
	case "/algorithm/search/script-params":
		response, callErr := fastapiv1.NewAlgorithmClient(connection).GetSearchScriptParams(callCtx, &fastapiv1.EmptyRequest{})
		return resultFromGrpc(response, callErr)
	case "/ai_history/internal/:id":
		request := buildJSONRequest(path, opts)
		client := fastapiv1.NewAiHistoryClient(connection)
		var response *commonv1.Result
		switch opts.Method {
		case "GET":
			response, err = client.Get(callCtx, request)
		case "PUT":
			response, err = client.Update(callCtx, request)
		case "DELETE":
			response, err = client.Delete(callCtx, request)
		default:
			return Result{}, errGrpcUnavailable
		}
		return resultFromGrpc(response, err)
	case "/article-logs/search-history/:user_id":
		response, callErr := nestjsv1.NewLogClient(connection).SearchHistory(callCtx, buildJSONRequest(path, opts))
		return resultFromGrpc(response, callErr)
	case "/articles/list":
		response, callErr := springv1.NewArticleClient(connection).List(callCtx, buildJSONRequest(path, opts))
		return resultFromGrpc(response, callErr)
	case "/articles/batch":
		response, callErr := springv1.NewArticleClient(connection).Batch(callCtx, buildJSONRequest(path, opts))
		return resultFromGrpc(response, callErr)
	case "/articles/views/batch":
		response, callErr := springv1.NewArticleClient(connection).ViewsBatch(callCtx, buildJSONRequest(path, opts))
		return resultFromGrpc(response, callErr)
	case "/category/batch":
		response, callErr := springv1.NewCategoryClient(connection).Batch(callCtx, buildJSONRequest(path, opts))
		return resultFromGrpc(response, callErr)
	case "/category/sub/batch":
		response, callErr := springv1.NewCategoryClient(connection).SubBatch(callCtx, buildJSONRequest(path, opts))
		return resultFromGrpc(response, callErr)
	case "/users/:id":
		response, callErr := springv1.NewUserClient(connection).Get(callCtx, buildJSONRequest(path, opts))
		return resultFromGrpc(response, callErr)
	case "/users/batch":
		response, callErr := springv1.NewUserClient(connection).Batch(callCtx, buildJSONRequest(path, opts))
		return resultFromGrpc(response, callErr)
	case "/users/by-name":
		response, callErr := springv1.NewUserClient(connection).ByName(callCtx, buildJSONRequest(path, opts))
		return resultFromGrpc(response, callErr)
	case "/users/by-github-id/:githubId":
		response, callErr := springv1.NewUserClient(connection).ByGithubId(callCtx, buildJSONRequest(path, opts))
		return resultFromGrpc(response, callErr)
	case "/users/github-user":
		response, callErr := springv1.NewUserClient(connection).GithubUser(callCtx, buildJSONRequest(path, opts))
		return resultFromGrpc(response, callErr)
	case "/users/:id/is-admin":
		response, callErr := springv1.NewUserClient(connection).IsAdmin(callCtx, buildJSONRequest(path, opts))
		return resultFromGrpc(response, callErr)
	case "/users/github/token-ticket":
		response, callErr := springv1.NewUserClient(connection).TokenTicket(callCtx, buildJSONRequest(path, opts))
		return resultFromGrpc(response, callErr)
	case "/comments/scores/batch":
		response, callErr := springv1.NewInteractionClient(connection).CommentScores(callCtx, buildJSONRequest(path, opts))
		return resultFromGrpc(response, callErr)
	case "/likes/counts/batch":
		response, callErr := springv1.NewInteractionClient(connection).LikeCounts(callCtx, buildJSONRequest(path, opts))
		return resultFromGrpc(response, callErr)
	case "/collects/counts/batch":
		response, callErr := springv1.NewInteractionClient(connection).CollectCounts(callCtx, buildJSONRequest(path, opts))
		return resultFromGrpc(response, callErr)
	case "/focus/counts/batch":
		response, callErr := springv1.NewInteractionClient(connection).FollowCounts(callCtx, buildJSONRequest(path, opts))
		return resultFromGrpc(response, callErr)
	default:
		return Result{}, errGrpcUnavailable
	}
}

func buildJSONRequest(path string, opts RequestOptions) *commonv1.JsonRequest {
	payload, _ := json.Marshal(map[string]any{
		"method": opts.Method,
		"route":  path,
		"path":   opts.PathParams,
		"query":  opts.QueryParams,
		"body":   opts.BodyData,
	})
	return &commonv1.JsonRequest{Payload: payload}
}

func (t *grpcTransport) connection(ctx context.Context, address string) (*grpc.ClientConn, error) {
	if value, ok := t.connections.Load(address); ok {
		return value.(*grpc.ClientConn), nil
	}
	connection, err := grpc.DialContext(ctx, address, grpc.WithTransportCredentials(insecure.NewCredentials()), grpc.WithBlock())
	if err != nil {
		return nil, err
	}
	actual, loaded := t.connections.LoadOrStore(address, connection)
	if loaded {
		_ = connection.Close()
		return actual.(*grpc.ClientConn), nil
	}
	return connection, nil
}

func resultFromGrpc(response *commonv1.Result, err error) (Result, error) {
	if err != nil {
		return Result{}, err
	}
	if response == nil {
		return Result{}, errors.New(constants.GRPC_RESPONSE_EMPTY)
	}
	result := Result{Code: int(response.Code), Msg: response.Message}
	if len(response.Data) > 0 {
		if err := json.Unmarshal(response.Data, &result.Data); err != nil {
			return Result{}, err
		}
	}
	if result.Code < 200 || result.Code >= 300 {
		return result, status.Error(codes.InvalidArgument, result.Msg)
	}
	return result, nil
}

func buildGraphRequest(data any) *fastapiv1.GraphEnhanceRequest {
	body := data.(map[string]any)
	return &fastapiv1.GraphEnhanceRequest{
		UserId: int64Value(body["user_id"]), Keyword: stringValue(body["keyword"]),
		ArticleIds: int64SliceValue(body["article_ids"]), CategoryName: stringValue(body["category_name"]),
		SubCategoryName: stringValue(body["sub_category_name"]), Tags: stringSliceValue(body["tags"]),
		Limit: int32(int64Value(body["limit"])), Mode: stringValue(body["mode"]),
	}
}

func buildVectorRequest(data any) *fastapiv1.VectorEnhanceRequest {
	body := data.(map[string]any)
	return &fastapiv1.VectorEnhanceRequest{
		UserId: int64Value(body["user_id"]), Keyword: stringValue(body["keyword"]),
		ArticleIds: int64SliceValue(body["article_ids"]), CategoryName: stringValue(body["category_name"]),
		SubCategoryName: stringValue(body["sub_category_name"]), Tags: stringSliceValue(body["tags"]),
		Limit: int32(int64Value(body["limit"])), TopK: int32(int64Value(body["top_k"])), Mode: stringValue(body["mode"]),
	}
}

func int64Value(value any) int64 {
	switch number := value.(type) {
	case int:
		return int64(number)
	case int64:
		return number
	case float64:
		return int64(number)
	default:
		return 0
	}
}

func int64SliceValue(value any) []int64 {
	values, ok := value.([]int64)
	if ok {
		return values
	}
	items, ok := value.([]any)
	if !ok {
		return nil
	}
	result := make([]int64, 0, len(items))
	for _, item := range items {
		result = append(result, int64Value(item))
	}
	return result
}

func stringValue(value any) string {
	result, _ := value.(string)
	return result
}

func stringSliceValue(value any) []string {
	result, _ := value.([]string)
	return result
}

func contextInt64(ctx context.Context, key any) int64 {
	value, _ := ctx.Value(key).(int64)
	return value
}

func contextString(ctx context.Context, key any) string {
	value, _ := ctx.Value(key).(string)
	return value
}

var errGrpcUnavailable = fmt.Errorf(constants.GRPC_CHANNEL_UNAVAILABLE)

func isGrpcChannelError(err error) bool {
	if errors.Is(err, errGrpcUnavailable) {
		return true
	}
	code := status.Code(err)
	return code == codes.Unavailable || code == codes.DeadlineExceeded
}

func logGrpcFallback(serviceName, path string, err error) {
	logx.Infof(constants.GRPC_CALL_FALLBACK, serviceName, path, err)
}
