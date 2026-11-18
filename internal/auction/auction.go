// Package auction implements a deliberately small, simulated first-price auction.
package auction

import (
	"strings"

	"github.com/rayning0/scenebid/internal/model"
)

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
			if strings.EqualFold(category, b.Category) {
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
		d.Reason = "highest eligible simulated bid meeting floor and matching scene category"
	}
	return d
}
