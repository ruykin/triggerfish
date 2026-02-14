package graph

type Edge struct {
	From     string
	To       string
	Type     string
	Metadata map[string]string
}
