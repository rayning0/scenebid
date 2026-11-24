package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"github.com/rayning0/scenebid/internal/analysis"
	"github.com/rayning0/scenebid/internal/auction"
	"github.com/rayning0/scenebid/internal/model"
	"github.com/rayning0/scenebid/internal/store"
	"log"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
)

const defaultBidFloorUSDCPM = 2.0

func main() {
	if len(os.Args) < 2 {
		usage()
	}
	switch os.Args[1] {
	case "analyze":
		f := flag.NewFlagSet("analyze", flag.ExitOnError)
		video := f.String("video", "data/input/TV_Commercials_1977.mp4", "local input video")
		out := f.String("out", "data/output/TV_Commercials_1977", "output directory")
		at := f.Float64("at", 5, "frame timestamp in seconds")
		worker := f.String("worker", "analysis-worker/main.py", "Python analysis worker")
		start := f.Float64("start", 0, "analysis start time in seconds")
		end := f.Float64("end", -1, "optional analysis end time; -1 processes the full video")
		_ = f.Parse(os.Args[2:])
		if *at < 0 {
			log.Fatal("frame timestamp must be nonnegative")
		}
		if err := analysis.Probe(*video, filepath.Join(*out, "probe.json")); err != nil {
			log.Fatal(err)
		}
		if err := analysis.Frame(*video, filepath.Join(*out, "frames", "sample.jpg"), *at); err != nil {
			log.Fatal(err)
		}
		args := []string{*worker, *video, *out, "--start", strconv.FormatFloat(*start, 'f', -1, 64)}
		if *end >= 0 {
			args = append(args, "--end", strconv.FormatFloat(*end, 'f', -1, 64))
		}
		cmd := exec.Command("python3", args...)
		cmd.Stdout, cmd.Stderr = os.Stdout, os.Stderr
		if err := cmd.Run(); err != nil {
			log.Fatalf("AI analysis worker failed: %v", err)
		}
		fmt.Printf("Analyzed video and wrote real AI annotations into %s\n", *out)
	case "decide":
		f := flag.NewFlagSet("decide", flag.ExitOnError)
		analysisPath := f.String("analysis", "data/output/TV_Commercials_1977/analysis.json", "worker analysis.json")
		campaignsPath := f.String("campaigns", "data/fixtures/campaigns.json", "fictional campaigns")
		out := f.String("out", "data/output/TV_Commercials_1977/decisions.json", "output JSON")
		floor := f.Float64("floor", defaultBidFloorUSDCPM, "minimum simulated USD CPM")
		_ = f.Parse(os.Args[2:])
		if *floor < 0 {
			log.Fatal("floor must be nonnegative")
		}
		var a model.Contract
		var campaigns struct {
			Campaigns []campaign `json:"campaigns"`
		}
		if err := store.Read(*analysisPath, &a); err != nil {
			log.Fatal(err)
		}
		if err := store.Read(*campaignsPath, &campaigns); err != nil {
			log.Fatal(err)
		}
		ds := make([]model.Decision, 0)
		opportunities := make([]map[string]interface{}, 0)
		for _, s := range a.Segments {
			ops := s.AdOpportunities
			for _, op := range ops {
				d := model.Decision{DecisionID: "decision-" + op.ID, VideoID: a.Video.ID,
					ContentTimeSec: op.StartSec, SegmentID: s.ID, OpportunityID: op.ID,
					Status: "no_fill"}
				scene := model.Scene{ID: s.ID, Safety: s.Intelligence.BrandSafety.Status}
				for _, cat := range s.Intelligence.Categories {
					scene.Categories = append(scene.Categories, cat.ID)
				}
				for _, entity := range s.Intelligence.Entities {
					scene.Categories = append(scene.Categories, entity.Name)
				}
				var bids []model.Bid
				for _, c := range campaigns.Campaigns {
					for _, cat := range c.TargetCategories {
						bids = append(bids, model.Bid{Campaign: c.ID, CPM: c.CPM, Category: cat, Advertiser: c.Advertiser, Headline: c.Headline, URL: c.URL, LogoURL: c.LogoURL})
					}
				}
				d = auction.DecideDemo(scene, bids, *floor)
				d.DecisionID = "decision-" + op.ID
				d.VideoID = a.Video.ID
				d.ContentTimeSec = op.StartSec
				d.OpportunityEndSec = op.EndSec
				d.SegmentID = s.ID
				d.OpportunityID = op.ID
				d.ModelSafety = s.Intelligence.BrandSafety.Status
				ds = append(ds, d)
				opportunities = append(opportunities, map[string]interface{}{"id": op.ID, "segment_id": s.ID, "start_sec": op.StartSec, "end_sec": op.EndSec, "categories": scene.Categories, "summary": s.Intelligence.Summary, "products": s.Intelligence.Entities})
			}
		}
		if err := store.Write(*out, ds); err != nil {
			log.Fatal(err)
		}
		_ = store.Write(filepath.Join(filepath.Dir(*out), "opportunities.json"), opportunities)
		fmt.Printf("Wrote %d simulated decisions to %s\n", len(ds), *out)
	case "serve":
		f := flag.NewFlagSet("serve", flag.ExitOnError)
		analysisPath := f.String("analysis", "data/output/TV_Commercials_1977/analysis.json", "analysis")
		campaignsPath := f.String("campaigns", "data/fixtures/campaigns.json", "campaigns")
		addr := f.String("addr", ":8080", "listen address")
		floor := f.Float64("floor", defaultBidFloorUSDCPM, "minimum simulated USD CPM")
		_ = f.Parse(os.Args[2:])
		if *floor < 0 {
			log.Fatal("floor must be nonnegative")
		}
		var a model.Contract
		var c struct {
			Campaigns []campaign `json:"campaigns"`
		}
		if err := store.Read(*analysisPath, &a); err != nil {
			log.Fatal(err)
		}
		if err := store.Read(*campaignsPath, &c); err != nil {
			log.Fatal(err)
		}
		var transcript []struct {
			StartSec float64 `json:"start_sec"`
			EndSec   float64 `json:"end_sec"`
			Text     string  `json:"text"`
		}
		if err := store.Read("data/output/TV_Commercials_1977/transcript.json", &transcript); err != nil {
			log.Fatal(err)
		}
		http.Handle("/", http.FileServer(http.Dir("web")))
		http.Handle("/media/TV_Commercials_1977.mp4", http.StripPrefix("/media/", http.FileServer(http.Dir("data/input"))))
		http.Handle("/media/", http.StripPrefix("/media/", http.FileServer(http.Dir("data/output/TV_Commercials_1977/hls"))))
		http.HandleFunc("/api/opportunities", func(w http.ResponseWriter, r *http.Request) {
			var opportunities []map[string]interface{}
			for _, s := range a.Segments {
				ops := s.AdOpportunities
				for _, op := range ops {
					opportunities = append(opportunities, map[string]interface{}{"id": op.ID, "start_sec": op.StartSec, "end_sec": op.EndSec})
				}
			}
			json.NewEncoder(w).Encode(opportunities)
		})
		http.HandleFunc("/api/context", func(w http.ResponseWriter, r *http.Request) {
			type contextItem struct {
				StartSec float64 `json:"start_sec"`
				EndSec   float64 `json:"end_sec"`
				Summary  string  `json:"summary,omitempty"`
				Text     string  `json:"text,omitempty"`
			}
			items := make([]contextItem, 0, len(transcript)+len(a.Segments))
			for _, line := range transcript {
				items = append(items, contextItem{StartSec: line.StartSec, EndSec: line.EndSec, Text: line.Text})
			}
			for _, segment := range a.Segments {
				if summary := segment.Intelligence.Summary; summary != "" {
					items = append(items, contextItem{StartSec: segment.StartSec, EndSec: segment.EndSec, Summary: summary})
				}
			}
			json.NewEncoder(w).Encode(items)
		})
		http.HandleFunc("/api/decision", func(w http.ResponseWriter, r *http.Request) {
			t, _ := strconv.ParseFloat(r.URL.Query().Get("time"), 64)
			for _, s := range a.Segments {
				if t >= s.StartSec && t < s.EndSec {
					if len(s.AdOpportunities) == 0 {
						continue
					}
					op := s.AdOpportunities[0]
					for _, x := range s.AdOpportunities {
						if t >= x.StartSec && t < x.EndSec {
							op = x
						}
					}
					if t >= op.StartSec && t < op.EndSec {
						scene := model.Scene{ID: s.ID, Safety: s.Intelligence.BrandSafety.Status}
						for _, x := range s.Intelligence.Categories {
							scene.Categories = append(scene.Categories, x.ID)
						}
						for _, entity := range s.Intelligence.Entities {
							scene.Categories = append(scene.Categories, entity.Name)
						}
						var bids []model.Bid
						for _, x := range c.Campaigns {
							for _, cat := range x.TargetCategories {
								bids = append(bids, model.Bid{Campaign: x.ID, CPM: x.CPM, Category: cat, Advertiser: x.Advertiser, Headline: x.Headline, URL: x.URL, LogoURL: x.LogoURL})
							}
						}
						d := auction.DecideDemo(scene, bids, *floor)
						d.VideoID = a.Video.ID
						d.ContentTimeSec = op.StartSec
						d.OpportunityEndSec = op.EndSec
						d.SegmentID = s.ID
						d.OpportunityID = op.ID
						d.ModelSafety = s.Intelligence.BrandSafety.Status
						json.NewEncoder(w).Encode(d)
						return
					}
				}
			}
			json.NewEncoder(w).Encode(model.Decision{Status: "no_fill", Reason: "no opportunity at playback time", DemoMode: true})
		})
		log.Printf("SceneBid demo at http://localhost%s", *addr)
		log.Fatal(http.ListenAndServe(*addr, nil))
	default:
		usage()
	}
}

type campaign struct {
	ID               string   `json:"id"`
	Name             string   `json:"name"`
	Advertiser       string   `json:"advertiser"`
	TargetCategories []string `json:"target_categories"`
	CPM              float64  `json:"bid_cpm_usd"`
	Headline         string   `json:"headline"`
	URL              string   `json:"destination_url"`
	LogoURL          string   `json:"logo_url"`
}

func min(a, b float64) float64 {
	if a < b {
		return a
	}
	return b
}

func usage() { fmt.Fprintln(os.Stderr, "usage: scenebid {analyze|decide} [options]"); os.Exit(2) }
