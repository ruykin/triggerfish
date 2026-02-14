package main

import (
	"log"
	"os"

	"github.com/sidshrivastav/triggerfish/core/internal/server"
)

func main() {
	log.SetOutput(os.Stderr)
	srv := server.New()
	if err := srv.Run(os.Stdin, os.Stdout); err != nil {
		log.Fatalf("Server error: %v", err)
	}
}
