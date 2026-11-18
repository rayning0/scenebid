// Package model holds the data shared by the pipeline and the simulated auction.
package model

type Scene struct {
	ID          string   `json:"id"`
	StartSec    float64  `json:"start_sec"`
	EndSec      float64  `json:"end_sec"`
	Description string   `json:"description"`
	Categories  []string `json:"categories"`
	Safety      string   `json:"safety"`
	Source      string   `json:"source"`
}

type Bid struct {
	Campaign string  `json:"campaign"`
	Source   string  `json:"source"`
	CPM      float64 `json:"cpm"`
	Category string  `json:"category"`
}

type Decision struct {
	SceneID        string  `json:"scene_id"`
	DecisionID     string  `json:"decision_id,omitempty"`
	VideoID        string  `json:"video_id,omitempty"`
	ContentTimeSec float64 `json:"content_time_sec,omitempty"`
	SegmentID      string  `json:"segment_id,omitempty"`
	OpportunityID  string  `json:"opportunity_id,omitempty"`
	Status         string  `json:"status,omitempty"`
	Winner         *Bid    `json:"winner,omitempty"`
	Reason         string  `json:"reason"`
	Candidates     []Bid   `json:"candidates"`
}
