package model

// Contract is the versioned Python-worker output consumed by decisioning.
type Contract struct {
	SchemaVersion string `json:"schema_version"`
	Video         struct {
		ID           string  `json:"id"`
		SourceFile   string  `json:"source_file"`
		DurationSec  float64 `json:"duration_sec"`
		TimelineUnit string  `json:"timeline_unit"`
	} `json:"video"`
	Segments []ContractSegment `json:"segments"`
}
type ContractSegment struct {
	ID             string  `json:"id"`
	Kind           string  `json:"kind"`
	StartSec       float64 `json:"start_sec"`
	EndSec         float64 `json:"end_sec"`
	AnalysisStatus string  `json:"analysis_status"`
	Intelligence   struct {
		Summary    string `json:"summary"`
		Categories []struct {
			ID string `json:"id"`
		} `json:"categories"`
		Entities []struct {
			Name string `json:"name"`
		} `json:"entities"`
		BrandSafety struct {
			Status string `json:"status"`
		} `json:"brand_safety"`
	} `json:"intelligence"`
	AdOpportunities []ContractOpportunity `json:"ad_opportunities"`
}
type ContractOpportunity struct {
	ID       string  `json:"id"`
	Format   string  `json:"format"`
	StartSec float64 `json:"start_sec"`
	EndSec   float64 `json:"end_sec"`
	Status   string  `json:"status"`
}
