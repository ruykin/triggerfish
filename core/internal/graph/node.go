package graph

type Node struct {
	ID       string
	Type     string
	Name     string
	FilePath string
	Line     int
	Column   int
	Metadata map[string]string
}
