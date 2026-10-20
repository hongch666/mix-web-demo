package search

import (
	"context"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"app/common/utils"

	"github.com/olivere/elastic/v7"
)

// TestBuildSearchDSLContainsQueryAndPaging 校验 DSL 拼装包含查询条件与分页参数
func TestBuildSearchDSLContainsQueryAndPaging(t *testing.T) {
	query := elastic.NewBoolQuery().Must(elastic.NewMatchQuery("title", "golang"))

	dsl, err := buildSearchDSL(query, 20, 10, false, nil)
	if err != nil {
		t.Fatalf("拼装 DSL 失败: %v", err)
	}

	for _, want := range []string{`"query"`, `"from":20`, `"size":10`, `"request_cache":true`, "golang"} {
		if !strings.Contains(dsl, want) {
			t.Fatalf("DSL 缺少片段 %s，实际内容: %s", want, dsl)
		}
	}

	if strings.Contains(dsl, `"sort"`) {
		t.Fatalf("无关键词时不应带排序，实际内容: %s", dsl)
	}
}

// TestBuildSearchDSLContainsSortWhenSortByCreateAt 校验按创建时间倒序时 DSL 带 sort
func TestBuildSearchDSLContainsSortWhenSortByCreateAt(t *testing.T) {
	dsl, err := buildSearchDSL(elastic.NewBoolQuery(), 0, 10, true, nil)
	if err != nil {
		t.Fatalf("拼装 DSL 失败: %v", err)
	}

	if !strings.Contains(dsl, `"create_at"`) || !strings.Contains(dsl, `"desc"`) {
		t.Fatalf("DSL 缺少创建时间倒序，实际内容: %s", dsl)
	}
}

// TestBuildSearchDSLContainsHighlight 校验有关键词时 DSL 带高亮配置
func TestBuildSearchDSLContainsHighlight(t *testing.T) {
	highlight := elastic.NewHighlight().PreTags("<em>").PostTags("</em>").
		Fields(elastic.NewHighlighterField("title")).
		FragmentSize(150)

	dsl, err := buildSearchDSL(elastic.NewBoolQuery(), 0, 10, false, highlight)
	if err != nil {
		t.Fatalf("拼装 DSL 失败: %v", err)
	}

	if !strings.Contains(dsl, `"highlight"`) || !strings.Contains(dsl, "title") {
		t.Fatalf("DSL 缺少高亮配置，实际内容: %s", dsl)
	}
}

// TestLogSearchDSLDisabledWritesNothing 校验开关关闭时不产生任何 DSL 日志
func TestLogSearchDSLDisabledWritesNothing(t *testing.T) {
	logDir := t.TempDir()
	logger, err := utils.NewZeroLogger(logDir)
	if err != nil {
		t.Fatalf("创建日志实例失败: %v", err)
	}
	defer logger.Close()

	model := &searchModel{dslLogEnabled: false, logger: logger}
	model.logSearchDSL(context.Background(), elastic.NewBoolQuery(), 0, 10, false, nil)

	entries, err := os.ReadDir(logDir)
	if err != nil {
		t.Fatalf("读取日志目录失败: %v", err)
	}
	if len(entries) != 0 {
		t.Fatalf("开关关闭时不应产生日志文件，实际文件数: %d", len(entries))
	}
}

// TestLogSearchDSLEnabledWritesDSL 校验开关开启时输出包含索引名与查询条件的 DSL 日志
func TestLogSearchDSLEnabledWritesDSL(t *testing.T) {
	logDir := t.TempDir()
	logger, err := utils.NewZeroLogger(logDir)
	if err != nil {
		t.Fatalf("创建日志实例失败: %v", err)
	}
	defer logger.Close()

	model := &searchModel{dslLogEnabled: true, logger: logger}
	model.logSearchDSL(context.Background(), elastic.NewMatchQuery("title", "golang"), 0, 10, false, nil)

	logFile := filepath.Join(logDir, "app_"+time.Now().Format("2006-01-02")+".log")
	content, err := os.ReadFile(logFile)
	if err != nil {
		t.Fatalf("读取日志文件失败: %v", err)
	}

	text := string(content)
	if !strings.Contains(text, "ES 查询 DSL") {
		t.Fatalf("日志缺少 DSL 标识，实际内容: %s", text)
	}
	if !strings.Contains(text, articlesIndexName) {
		t.Fatalf("日志缺少索引名，实际内容: %s", text)
	}
	if !strings.Contains(text, "golang") {
		t.Fatalf("日志缺少查询条件，实际内容: %s", text)
	}
}

// TestLogSearchDSLWithoutLoggerIsSafe 校验未装配日志实例时开启开关也不会 panic
func TestLogSearchDSLWithoutLoggerIsSafe(t *testing.T) {
	model := &searchModel{dslLogEnabled: true}
	model.logSearchDSL(context.Background(), elastic.NewBoolQuery(), 0, 10, false, nil)
}
