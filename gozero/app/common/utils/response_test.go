package utils_test

import (
	"encoding/json"
	"errors"
	"net/http/httptest"
	"strings"
	"testing"

	"app/common/constants"
	"app/common/utils"
)

type testBusinessError struct{}

type testDataResponse struct {
	Data string `json:"data"`
}

// testEmptyResponse 对应 .api 里 SyncESResp{} 这类零字段响应模型
type testEmptyResponse struct{}

type testPlainResponse struct {
	Total int `json:"total"`
}

func (testBusinessError) Error() string           { return "business failure" }
func (testBusinessError) BusinessCode() int       { return 422 }
func (testBusinessError) BusinessMessage() string { return "invalid input" }

func decodeResponse(t *testing.T, recorder *httptest.ResponseRecorder) map[string]any {
	t.Helper()
	var body map[string]any
	if err := json.NewDecoder(recorder.Body).Decode(&body); err != nil {
		t.Fatalf("decode response: %v", err)
	}
	return body
}

// 验证该测试场景的预期行为

func TestSuccessAndErrorResponses(t *testing.T) {
	successRecorder := httptest.NewRecorder()
	utils.Success(successRecorder, map[string]any{"id": 7})
	if successRecorder.Code != 200 {
		t.Fatalf("success status = %d", successRecorder.Code)
	}
	successBody := decodeResponse(t, successRecorder)
	if successBody["code"] != float64(constants.HttpOK) || successBody["msg"] != "success" {
		t.Fatalf("unexpected success body: %#v", successBody)
	}
	if payload, ok := successBody["data"].(map[string]any); !ok || payload["id"] != float64(7) {
		t.Fatalf("unexpected success data: %#v", successBody["data"])
	}

	modelRecorder := httptest.NewRecorder()
	utils.Success(modelRecorder, &testDataResponse{Data: "hello"})
	modelBody := decodeResponse(t, modelRecorder)
	if modelBody["data"] != "hello" {
		t.Fatalf("expected Data field to be unwrapped: %#v", modelBody)
	}

	errorRecorder := httptest.NewRecorder()
	utils.Error(errorRecorder, 400, "bad request")
	if errorRecorder.Code != 400 {
		t.Fatalf("error status = %d", errorRecorder.Code)
	}
	errorBody := decodeResponse(t, errorRecorder)
	if errorBody["code"] != float64(400) || errorBody["msg"] != "bad request" {
		t.Fatalf("unexpected error body: %#v", errorBody)
	}
}

// 验证该测试场景的预期行为

func TestHandleErrorUsesBusinessOrInternalStatus(t *testing.T) {
	businessRecorder := httptest.NewRecorder()
	utils.HandleError(businessRecorder, testBusinessError{})
	if businessRecorder.Code != 422 {
		t.Fatalf("business status = %d", businessRecorder.Code)
	}

	internalRecorder := httptest.NewRecorder()
	utils.HandleError(internalRecorder, errors.New("database unavailable"))
	if internalRecorder.Code != constants.HttpInternalServerError {
		t.Fatalf("internal status = %d", internalRecorder.Code)
	}
}

// 验证该测试场景的预期行为

func TestHandleErrorWithCodeUsesDefaultStatusForRegularErrors(t *testing.T) {
	recorder := httptest.NewRecorder()
	utils.HandleErrorWithCode(recorder, errors.New("invalid payload"), 400)
	if recorder.Code != 400 {
		t.Fatalf("status = %d, want 400", recorder.Code)
	}
	body := decodeResponse(t, recorder)
	if body["msg"] != "invalid payload" || body["data"] != nil {
		t.Fatalf("unexpected response body: %#v", body)
	}
}

// 零字段响应模型（SyncESResp 这类空壳）必须输出 data 为 null，
// 文档与 NestJS 的空数据响应都声明为 null，不能被序列化成空对象
func TestSuccessWritesNullDataForEmptyResponseModel(t *testing.T) {
	recorder := httptest.NewRecorder()
	utils.Success(recorder, &testEmptyResponse{})

	// 先取原始报文再解析：解析会消费 Body 缓冲
	raw := recorder.Body.String()
	if !strings.Contains(raw, `"data":null`) {
		t.Fatalf("expected raw null data in body: %s", raw)
	}

	body := decodeResponse(t, recorder)
	if body["data"] != nil {
		t.Fatalf("expected null data for empty response model: %#v", body)
	}
}

// 有字段但没有 Data 字段的响应模型仍应原样输出整个结构体，不能一并置空
func TestSuccessKeepsPlainResponseModel(t *testing.T) {
	recorder := httptest.NewRecorder()
	utils.Success(recorder, &testPlainResponse{Total: 3})

	body := decodeResponse(t, recorder)
	payload, ok := body["data"].(map[string]any)
	if !ok || payload["total"] != float64(3) {
		t.Fatalf("expected plain payload to be kept: %#v", body)
	}
}
