// Package analysis extracts real media metadata and a frame; it does not infer scene meaning.
package analysis

import (
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
)

func Probe(video, output string) error {
	cmd := exec.Command("ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", video)
	b, err := cmd.Output(); if err != nil { return fmt.Errorf("ffprobe: %w", err) }
	var v any; if err := json.Unmarshal(b, &v); err != nil { return err }
	if err := os.MkdirAll(filepath.Dir(output), 0755); err != nil { return err }
	return os.WriteFile(output, b, 0644)
}

func Frame(video, output string, seconds float64) error {
	if err := os.MkdirAll(filepath.Dir(output), 0755); err != nil { return err }
	cmd := exec.Command("ffmpeg", "-y", "-ss", fmt.Sprintf("%.3f", seconds), "-i", video, "-frames:v", "1", output)
	if b, err := cmd.CombinedOutput(); err != nil { return fmt.Errorf("ffmpeg: %w: %s", err, b) }; return nil
}
