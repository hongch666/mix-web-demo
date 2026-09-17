package search

import (
	"context"
	"errors"
	"math"
	"testing"

	commonclient "app/common/client"
	"app/common/utils"
	"app/internal/client/fastapiClient"
	"app/internal/svc"
	"app/internal/types"
	searchmodel "app/model/search"
)

// TestResolveRecallWindow 校验召回窗口解析与深分页降级边界
func TestResolveRecallWindow(t *testing.T) {
	cases := []struct {
		name          string
		page          int
		size          int
		wantPage      int
		wantRecall    int
		wantAmplified bool
	}{
		{name: "首页放大召回", page: 1, size: 10, wantPage: 1, wantRecall: 100, wantAmplified: true},
		{name: "同档位内各页共享候选集", page: 10, size: 10, wantPage: 1, wantRecall: 100, wantAmplified: true},
		{name: "跨入下一档位", page: 11, size: 10, wantPage: 1, wantRecall: 200, wantAmplified: true},
		{name: "档位上限边界", page: 20, size: 10, wantPage: 1, wantRecall: 200, wantAmplified: true},
		{name: "超出召回上限退化为窗口内重排", page: 21, size: 10, wantPage: 21, wantRecall: 10, wantAmplified: false},
		{name: "大页尺寸单页放大", page: 1, size: 100, wantPage: 1, wantRecall: 100, wantAmplified: true},
		{name: "大页尺寸恰好到上限", page: 2, size: 100, wantPage: 1, wantRecall: 200, wantAmplified: true},
		{name: "大页尺寸超上限退化", page: 5, size: 50, wantPage: 5, wantRecall: 50, wantAmplified: false},
	}

	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			page, recallSize, amplified := resolveRecallWindow(c.page, c.size)
			if page != c.wantPage || recallSize != c.wantRecall || amplified != c.wantAmplified {
				t.Fatalf("resolveRecallWindow(%d, %d) = (%d, %d, %v), 期望 (%d, %d, %v)",
					c.page, c.size, page, recallSize, amplified, c.wantPage, c.wantRecall, c.wantAmplified)
			}

			// 放大开启时召回条数必须覆盖目标页窗口，否则切页会丢候选
			if amplified && recallSize < c.page*c.size {
				t.Fatalf("recallSize %d 无法覆盖 page*size %d", recallSize, c.page*c.size)
			}
		})
	}
}

// TestPageSlice 校验分页切片边界
func TestPageSlice(t *testing.T) {
	items := make([]types.ArticleEsItem, 25)
	for i := range items {
		items[i].Id = int64(i + 1)
	}

	cases := []struct {
		name      string
		page      int
		size      int
		wantLen   int
		wantFirst int64
	}{
		{name: "首页", page: 1, size: 10, wantLen: 10, wantFirst: 1},
		{name: "末页不足一页", page: 3, size: 10, wantLen: 5, wantFirst: 21},
		{name: "窗口越界返回空列表", page: 4, size: 10, wantLen: 0, wantFirst: 0},
		{name: "单页覆盖全部候选", page: 1, size: 100, wantLen: 25, wantFirst: 1},
	}

	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			got := pageSlice(items, c.page, c.size)
			if len(got) != c.wantLen {
				t.Fatalf("pageSlice 长度 = %d, 期望 %d", len(got), c.wantLen)
			}
			if c.wantLen > 0 && got[0].Id != c.wantFirst {
				t.Fatalf("pageSlice 首元素 Id = %d, 期望 %d", got[0].Id, c.wantFirst)
			}
		})
	}
}

// TestFusionMeanFillAndWeights 校验缺失信号均值填充与融合权重归一
func TestFusionMeanFillAndWeights(t *testing.T) {
	vectorItems := []fastapiClient.VectorEnhanceItem{
		{ArticleID: 1, VectorScore: 0.8},
		{ArticleID: 2, VectorScore: 1.2},
		{ArticleID: 3, VectorScore: -0.2},
	}

	// clamp01 后为 0.8 / 1.0 / 0.0，均值应为 0.6
	if got := meanOfVectorItems(vectorItems); math.Abs(got-0.6) > 1e-9 {
		t.Fatalf("meanOfVectorItems = %v, 期望 0.6", got)
	}

	if got := meanOfVectorItems(nil); got != 0 {
		t.Fatalf("meanOfVectorItems(nil) = %v, 期望 0", got)
	}

	graphItems := []fastapiClient.GraphEnhanceItem{
		{ArticleID: 1, GraphScore: 0.4},
	}
	if got := meanOfGraphItems(graphItems); math.Abs(got-0.4) > 1e-9 {
		t.Fatalf("meanOfGraphItems = %v, 期望 0.4", got)
	}

	engine := NewFusionEngine(FusionConfig{
		VectorScoreWeight: 0.3,
		GraphScoreWeight:  0.35,
		HybridMinESWeight: 0.1,
		IsLoggedIn:        true,
		HasKeyword:        true,
		VectorEnabled:     true,
		GraphEnabled:      true,
	})

	sum := engine.esWeight + engine.vectorWeight + engine.graphWeight
	if math.Abs(sum-1) > 1e-9 {
		t.Fatalf("融合权重之和 = %v, 期望 1", sum)
	}

	if engine.esWeight < 0.1-1e-9 {
		t.Fatalf("ES 权重 %v 低于最小保护值 0.1", engine.esWeight)
	}
}

func TestSearchArticlesUsesAmplifiedRecallThenSlicesRequestedPage(t *testing.T) {
	mode := "keyword"
	articles := make([]searchmodel.ArticleES, 25)
	for i := range articles {
		articles[i] = searchmodel.ArticleES{ID: int64(i + 1), ESScore: float64(25 - i)}
	}
	model := &searchModelStub{articles: articles, total: 25}
	client := &fastapiClientStub{
		script:   searchmodel.SearchScript{EsScript: "return 1"},
		weights:  searchmodel.SearchWeights{ESScoreWeight: 1},
		paramMap: searchmodel.ScriptParamMapping{"es_score_weight": "esWeight"},
	}
	logic, cleanup := newSearchLogicForTest(t, model, client)
	defer cleanup()

	response, err := logic.SearchArticles(&types.SearchArticlesReq{
		Page: 2,
		Size: 10,
		Mode: &mode,
	})
	if err != nil {
		t.Fatalf("搜索失败: %v", err)
	}
	if model.searchDTO.Page != 1 || model.searchDTO.Size != 100 {
		t.Fatalf("ES 召回窗口 = page %d size %d, 期望 page 1 size 100", model.searchDTO.Page, model.searchDTO.Size)
	}
	if len(response.List) != 10 || response.List[0].Id != 11 || response.List[9].Id != 20 {
		t.Fatalf("目标页切片错误: %+v", response.List)
	}
	if response.Total != 25 {
		t.Fatalf("总数 = %d, 期望 25", response.Total)
	}
}

func TestSearchArticlesDegradesToRequestedESPageWhenScriptFetchFails(t *testing.T) {
	model := &searchModelStub{
		articles: []searchmodel.ArticleES{{ID: 31, ESScore: 2}, {ID: 32, ESScore: 1}},
		total:    12,
	}
	client := &fastapiClientStub{scriptErr: errors.New("script unavailable")}
	logic, cleanup := newSearchLogicForTest(t, model, client)
	defer cleanup()

	response, err := logic.SearchArticles(&types.SearchArticlesReq{Page: 3, Size: 5})
	if err != nil {
		t.Fatalf("降级搜索失败: %v", err)
	}
	if model.searchDTO.Page != 3 || model.searchDTO.Size != 5 {
		t.Fatalf("降级查询分页 = page %d size %d, 期望 page 3 size 5", model.searchDTO.Page, model.searchDTO.Size)
	}
	if model.esScript != "" || model.weights != nil {
		t.Fatalf("降级查询不应传入脚本和权重: script=%q weights=%+v", model.esScript, model.weights)
	}
	if len(response.List) != 2 || response.List[0].Id != 31 {
		t.Fatalf("降级结果不应再次切页: %+v", response.List)
	}
}

type searchModelStub struct {
	articles  []searchmodel.ArticleES
	total     int
	err       error
	searchDTO searchmodel.ArticleSearchDTO
	esScript  string
	weights   *searchmodel.SearchWeights
}

func (s *searchModelStub) SearchArticle(
	_ context.Context,
	searchDTO searchmodel.ArticleSearchDTO,
	esScript string,
	weights *searchmodel.SearchWeights,
	_ searchmodel.ScriptParamMapping,
) ([]searchmodel.ArticleES, int, error) {
	s.searchDTO = searchDTO
	s.esScript = esScript
	s.weights = weights
	return s.articles, s.total, s.err
}

type fastapiClientStub struct {
	script    searchmodel.SearchScript
	weights   searchmodel.SearchWeights
	paramMap  searchmodel.ScriptParamMapping
	scriptErr error
}

func (s *fastapiClientStub) GetSearchScript(context.Context) (searchmodel.SearchScript, error) {
	return s.script, s.scriptErr
}

func (s *fastapiClientStub) GetSearchWeights(context.Context) (searchmodel.SearchWeights, error) {
	return s.weights, nil
}

func (s *fastapiClientStub) GetSearchScriptParams(context.Context) (searchmodel.ScriptParamMapping, error) {
	return s.paramMap, nil
}

func (s *fastapiClientStub) EnhanceGraph(context.Context, *fastapiClient.GraphEnhanceRequest) (commonclient.Result, error) {
	return commonclient.Result{}, nil
}

func (s *fastapiClientStub) EnhanceVector(context.Context, *fastapiClient.VectorEnhanceRequest) (commonclient.Result, error) {
	return commonclient.Result{}, nil
}

func (s *fastapiClientStub) GetAiHistoryByID(context.Context, int64) (commonclient.Result, error) {
	return commonclient.Result{}, nil
}

func (s *fastapiClientStub) UpdateAiHistory(context.Context, int64, *fastapiClient.UpdateAiHistoryRequest) (commonclient.Result, error) {
	return commonclient.Result{}, nil
}

func (s *fastapiClientStub) DeleteAiHistory(context.Context, int64) (commonclient.Result, error) {
	return commonclient.Result{}, nil
}

func newSearchLogicForTest(
	t *testing.T,
	model searchmodel.SearchModel,
	client fastapiClient.Client,
) (*SearchArticlesLogic, func()) {
	t.Helper()
	logger, err := utils.NewZeroLogger(t.TempDir())
	if err != nil {
		t.Fatalf("创建测试日志失败: %v", err)
	}
	serviceContext := &svc.ServiceContext{
		ModelContext:  &svc.ModelContext{SearchModel: model},
		ClientContext: &svc.ClientContext{FastapiClient: client},
		LoggerContext: &svc.LoggerContext{Logger: logger},
	}
	logic := &SearchArticlesLogic{
		ctx:        context.Background(),
		svcCtx:     serviceContext,
		ZeroLogger: logger,
	}
	return logic, func() {
		_ = logger.Close()
	}
}
