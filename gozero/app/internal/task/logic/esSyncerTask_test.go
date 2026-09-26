package logic

import (
	"context"
	"testing"

	"app/internal/svc"
	"app/model/search"
)

func TestSyncArticlesToESRejectsMissingClient(t *testing.T) {
	err := SyncArticlesToES(context.Background(), &svc.ServiceContext{
		InfrastructureContext: &svc.InfrastructureContext{},
		LoggerContext:         &svc.LoggerContext{},
	})
	if err == nil {
		t.Fatal("missing Elasticsearch client should return an error")
	}
}

func TestNormalizeESDateSupportsISOAndTargetFormats(t *testing.T) {
	tests := []struct{ input, expected string }{
		{"2025-07-16T23:00:50", "2025-07-16 23:00:50"},
		{"2025-07-16T23:00:50Z", "2025-07-16 23:00:50"},
		{"2025-07-16 23:00:50", "2025-07-16 23:00:50"},
		{"invalid", "invalid"},
		{"", ""},
	}
	for _, test := range tests {
		if actual := normalizeESDate(test.input); actual != test.expected {
			t.Fatalf("normalizeESDate(%q) = %q, want %q", test.input, actual, test.expected)
		}
	}
}

func TestToESDatePtrUsesNilForEmptyDate(t *testing.T) {
	if toESDatePtr("") != nil {
		t.Fatal("empty date should map to nil")
	}
	value := toESDatePtr("2025-07-16T23:00:50")
	if value == nil || *value != "2025-07-16 23:00:50" {
		t.Fatalf("unexpected normalized date pointer: %v", value)
	}
}

func TestHashArticleESIsStableAndChangesWithDocument(t *testing.T) {
	first := search.ArticleES{ID: 7, Title: "first"}
	second := search.ArticleES{ID: 7, Title: "second"}
	one, err := hashArticleES(first)
	if err != nil {
		t.Fatal(err)
	}
	two, err := hashArticleES(first)
	if err != nil {
		t.Fatal(err)
	}
	if one != two {
		t.Fatal("same document should produce stable hash")
	}
	three, err := hashArticleES(second)
	if err != nil {
		t.Fatal(err)
	}
	if one == three {
		t.Fatal("different documents should produce different hashes")
	}
}
