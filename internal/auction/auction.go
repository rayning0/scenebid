// Package auction implements a deliberately small, simulated first-price auction.
package auction

import (
	"strings"

	"github.com/rayning0/scenebid/internal/model"
)

var aliases = map[string]string{"camera": "cameras", "photography": "photography", "food": "food", "foods": "food"}

func canonical(v string) string {
	v = strings.ToLower(strings.TrimSpace(v))
	if x, ok := aliases[v]; ok {
		return x
	}
	return v
}

// Decide chooses the highest eligible CPM; equal bids retain input order.
// The floor and bids are simulated USD CPM. This is not an OpenRTB implementation.
func Decide(scene model.Scene, bids []model.Bid, floor float64) model.Decision {
	d := model.Decision{SceneID: scene.ID, Candidates: bids, Reason: "no eligible bid"}
	if scene.Safety != "safe" {
		d.Reason = "scene not explicitly marked safe"
		return d
	}
	for i := range bids {
		b := &bids[i]
		if b.CPM < floor {
			continue
		}
		match := false
		for _, category := range scene.Categories {
			if canonical(category) == canonical(b.Category) {
				match = true
				break
			}
		}
		if match && (d.Winner == nil || b.CPM > d.Winner.CPM) {
			copy := *b
			d.Winner = &copy
		}
	}
	if d.Winner != nil {
		d.Status = "filled"
		d.Reason = "highest eligible simulated bid meeting floor and matching scene category"
	} else {
		d.Status = "no_fill"
	}
	return d
}

// DecideDemo intentionally ignores the model safety value for this local demo,
// while retaining it in the returned decision trace.
func DecideDemo(scene model.Scene, bids []model.Bid, floor float64) model.Decision {
	original := scene.Safety
	scene.Safety = "safe"
	d := Decide(scene, bids, floor)
	d.DemoMode, d.ModelSafety = true, original
	d.Reason = "DEMO MODE: model safety ignored; " + d.Reason
	return d
}
