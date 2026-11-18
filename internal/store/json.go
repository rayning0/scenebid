package store

import (
	"encoding/json"
	"os"
	"path/filepath"
)

func Read(path string, target any) error {
	b, err := os.ReadFile(path); if err != nil { return err }; return json.Unmarshal(b, target)
}

func Write(path string, value any) error {
	if err := os.MkdirAll(filepath.Dir(path), 0755); err != nil { return err }
	b, err := json.MarshalIndent(value, "", "  "); if err != nil { return err }
	return os.WriteFile(path, append(b, '\n'), 0644)
}
