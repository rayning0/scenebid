package auction

import (
	"testing"

	"github.com/rayning0/scenebid/internal/model"
)

func TestDecide(t *testing.T) {
	bids := []model.Bid{{Campaign: "food", Category: "food", CPM: 5}, {Campaign: "other", Category: "cars", CPM: 10}, {Campaign: "low", Category: "food", CPM: 1}}
	s := model.Scene{ID: "s1", Safety: "safe", Categories: []string{"food"}}
	got := Decide(s, bids, 2)
	if got.Winner == nil || got.Winner.Campaign != "food" {
		t.Fatalf("unexpected decision: %+v", got)
	}
	s.Safety = "unknown"
	if got := Decide(s, bids, 2); got.Winner != nil {
		t.Fatalf("unknown safety must produce no fill: %+v", got)
	}
}

func TestDemoAliasesAndSafetyTrace(t *testing.T) {
	got := DecideDemo(model.Scene{ID: "w", Safety: "unknown", Categories: []string{"camera"}},
		[]model.Bid{{Campaign: "camera", Category: "cameras", CPM: 5}}, 2)
	if got.Winner == nil || got.Winner.Campaign != "camera" || !got.DemoMode || got.ModelSafety != "unknown" {
		t.Fatalf("demo decision did not preserve safety or alias-match: %+v", got)
	}
}

func TestNoFillBelowFloor(t *testing.T) {
	got := DecideDemo(model.Scene{ID: "w", Safety: "safe", Categories: []string{"food"}},
		[]model.Bid{{Campaign: "cheap", Category: "food", CPM: 1}}, 2)
	if got.Winner != nil || got.Status != "no_fill" {
		t.Fatalf("expected no fill at floor boundary: %+v", got)
	}
}
