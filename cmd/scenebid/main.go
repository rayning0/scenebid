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
	"path/filepath"
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
		fmt.Printf("Extracted video metadata and a frame at %.3fs into %s\n", *at, *out)
		fmt.Println("No AI classification was performed. Use the simulated fixtures for the auction demo.")
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
