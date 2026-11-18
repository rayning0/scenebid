package main

import (
	"flag"
	"fmt"
	"github.com/rayning0/scenebid/internal/analysis"
	"github.com/rayning0/scenebid/internal/model"
	"github.com/rayning0/scenebid/internal/store"
	"log"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
)

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
		floor := f.Float64("floor", 2, "minimum simulated USD CPM")
		_ = f.Parse(os.Args[2:])
		if *floor < 0 {
			log.Fatal("floor must be nonnegative")
		}
		var a model.Contract
		var campaigns struct {
			Campaigns []struct {
				ID         string   `json:"id"`
				Categories []string `json:"target_categories"`
				CPM        float64  `json:"bid_cpm_usd"`
			} `json:"campaigns"`
		}
		if err := store.Read(*analysisPath, &a); err != nil {
			log.Fatal(err)
		}
		if err := store.Read(*campaignsPath, &campaigns); err != nil {
			log.Fatal(err)
		}
		ds := make([]model.Decision, 0)
		for _, s := range a.Segments {
			for _, op := range s.AdOpportunities {
				d := model.Decision{DecisionID: "decision-" + op.ID, VideoID: a.Video.ID,
					ContentTimeSec: op.StartSec, SegmentID: s.ID, OpportunityID: op.ID,
					Status: "no_fill", Reason: "Brand-safety status is unknown."}
				if s.Intelligence.BrandSafety.Status == "safe" {
					for _, c := range campaigns.Campaigns {
						for _, cat := range s.Intelligence.Categories {
							matches := false
							for _, target := range c.Categories {
								matches = matches || strings.EqualFold(cat.ID, target)
							}
							if matches && c.CPM >= *floor {
								d.Status, d.Reason = "filled", "highest eligible campaign bid"
								d.Winner = &model.Bid{Campaign: c.ID, CPM: c.CPM, Category: cat.ID}
							}
						}
					}
				}
				ds = append(ds, d)
			}
		}
		if err := store.Write(*out, ds); err != nil {
			log.Fatal(err)
		}
		fmt.Printf("Wrote %d simulated decisions to %s\n", len(ds), *out)
	default:
		usage()
	}
}

func usage() { fmt.Fprintln(os.Stderr, "usage: scenebid {analyze|decide} [options]"); os.Exit(2) }
