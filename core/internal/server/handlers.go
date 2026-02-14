package server

import "encoding/json"

func (s *Server) dispatch(req Request) *Response {
	switch req.Method {
	case "health":
		return s.handleHealth(req)
	case "index_file":
		return s.handleIndexFile(req)
	case "find_symbol":
		return s.handleFindSymbol(req)
	case "neighbors":
		return s.handleNeighbors(req)
	default:
		return &Response{
			ID:    req.ID,
			Error: &Error{Code: -32601, Message: "Method not found"},
		}
	}
}

type HealthResult struct {
	Status  string `json:"status"`
	Version string `json:"version"`
}

func (s *Server) handleHealth(req Request) *Response {
	return &Response{
		ID:     req.ID,
		Result: HealthResult{Status: "ok", Version: "0.1.0"},
	}
}

type IndexFileParams struct {
	Path    string `json:"path"`
	Content string `json:"content"`
}

func (s *Server) handleIndexFile(req Request) *Response {
	var params IndexFileParams
	if err := json.Unmarshal(req.Params, &params); err != nil {
		return &Response{ID: req.ID, Error: &Error{Code: -32602, Message: "Invalid params"}}
	}

	if err := s.graph.IndexFile(params.Path, params.Content); err != nil {
		return &Response{ID: req.ID, Error: &Error{Code: -32000, Message: err.Error()}}
	}

	return &Response{
		ID:     req.ID,
		Result: map[string]interface{}{"indexed": true, "node_count": 1},
	}
}

type FindSymbolParams struct {
	Query string `json:"query"`
}

func (s *Server) handleFindSymbol(req Request) *Response {
	var params FindSymbolParams
	if err := json.Unmarshal(req.Params, &params); err != nil {
		return &Response{ID: req.ID, Error: &Error{Code: -32602, Message: "Invalid params"}}
	}

	nodes := s.graph.FindSymbol(params.Query)
	return &Response{
		ID:     req.ID,
		Result: map[string]interface{}{"nodes": nodes},
	}
}

type NeighborsParams struct {
	NodeID string `json:"node_id"`
}

func (s *Server) handleNeighbors(req Request) *Response {
	var params NeighborsParams
	if err := json.Unmarshal(req.Params, &params); err != nil {
		return &Response{ID: req.ID, Error: &Error{Code: -32602, Message: "Invalid params"}}
	}

	nodes := s.graph.Neighbors(params.NodeID)
	return &Response{
		ID:     req.ID,
		Result: map[string]interface{}{"nodes": nodes},
	}
}
