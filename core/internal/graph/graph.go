package graph

import "sync"

type Graph struct {
	mu    sync.RWMutex
	nodes map[string]*Node
	edges map[string][]*Edge
}

func New() *Graph {
	return &Graph{
		nodes: make(map[string]*Node),
		edges: make(map[string][]*Edge),
	}
}

func (g *Graph) IndexFile(path, content string) error {
	g.mu.Lock()
	defer g.mu.Unlock()

	node := &Node{
		ID:       path,
		Type:     "file",
		Name:     path,
		FilePath: path,
		Metadata: make(map[string]string),
	}
	g.nodes[path] = node
	return nil
}

func (g *Graph) FindSymbol(query string) []*Node {
	g.mu.RLock()
	defer g.mu.RUnlock()

	var results []*Node
	for _, node := range g.nodes {
		if node.Name == query {
			results = append(results, node)
		}
	}
	return results
}

func (g *Graph) Neighbors(nodeID string) []*Node {
	g.mu.RLock()
	defer g.mu.RUnlock()

	var neighbors []*Node
	for _, edge := range g.edges[nodeID] {
		if target, exists := g.nodes[edge.To]; exists {
			neighbors = append(neighbors, target)
		}
	}
	return neighbors
}
