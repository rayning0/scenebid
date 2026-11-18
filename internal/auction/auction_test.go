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
