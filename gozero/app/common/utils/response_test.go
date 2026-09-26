package utils_test

import (
	"encoding/json"
	"errors"
	"net/http/httptest"
	"testing"

	"app/common/constants"
	"app/common/utils"
)

type testBusinessError struct{}

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
