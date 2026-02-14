package server

import (
	"bufio"
	"encoding/json"
	"io"

	"github.com/sidshrivastav/triggerfish/core/internal/graph"
)

type Server struct {
	graph *graph.Graph
}

func New() *Server {
	return &Server{graph: graph.New()}
}

func (s *Server) Run(stdin io.Reader, stdout io.Writer) error {
	scanner := bufio.NewScanner(stdin)
	writer := bufio.NewWriter(stdout)

	for scanner.Scan() {
		response := s.handleRequest(scanner.Bytes())
		data, _ := json.Marshal(response)
		writer.Write(data)
		writer.WriteString("\n")
		writer.Flush()
	}
	return scanner.Err()
}

func (s *Server) handleRequest(data []byte) *Response {
	var req Request
	if err := json.Unmarshal(data, &req); err != nil {
		return &Response{Error: &Error{Code: -32700, Message: "Parse error"}}
	}
	return s.dispatch(req)
}
