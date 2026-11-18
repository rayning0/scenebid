package main

import (
	"flag"
	"fmt"
	"github.com/rayning0/scenebid/internal/analysis"
	"github.com/rayning0/scenebid/internal/auction"
	"github.com/rayning0/scenebid/internal/model"
	"github.com/rayning0/scenebid/internal/store"
	"log"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
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
		end := f.Float64("end", 30, "analysis end time; use -1 for the full video")
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
		scenes := f.String("scenes", "data/fixtures/scenes.json", "simulated scene annotations")
		bids := f.String("bids", "data/fixtures/bids.json", "simulated bids")
		out := f.String("out", "data/output/TV_Commercials_1977/decisions.json", "output JSON")
		floor := f.Float64("floor", 2, "minimum simulated USD CPM")
		_ = f.Parse(os.Args[2:])
		if *floor < 0 {
			log.Fatal("floor must be nonnegative")
		}
		var ss []model.Scene
		var bs []model.Bid
		if err := store.Read(*scenes, &ss); err != nil {
			log.Fatal(err)
		}
		if err := store.Read(*bids, &bs); err != nil {
			log.Fatal(err)
		}
		ds := make([]model.Decision, 0, len(ss))
		for _, s := range ss {
			ds = append(ds, auction.Decide(s, bs, *floor))
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
