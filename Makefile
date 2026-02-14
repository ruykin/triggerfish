.PHONY: all core-build smoke dev nix-update nix-check clean help

all: help

core-build:
	@echo "Building Go core..."
	cd core && go build -o triggerfish-core ./cmd/triggerfish-core
	@echo "✓ Built: core/triggerfish-core"

smoke: core-build
	@echo "Running smoke test..."
	@echo '{"id":"test","method":"health","params":{}}' | ./core/triggerfish-core | grep -q '"status":"ok"' && \
		echo "✓ Smoke test passed" || (echo "✗ Failed" && exit 1)

dev:
	@echo "Development Guide"
	@echo "================="
	@echo "Setup: nix develop"
	@echo "Build: make core-build"
	@echo "Test:  make smoke"
	@echo "LSP:   cd lsp && python -m triggerfish"

nix-update:
	nix flake update

nix-check:
	nix flake check && nix flake show

clean:
	rm -f core/triggerfish-core
	cd core && go clean

help:
	@echo "Available targets:"
	@echo "  make core-build  - Build Go core"
	@echo "  make smoke       - Test health endpoint"
	@echo "  make dev         - Show dev guide"
	@echo "  make nix-update  - Update flake.lock"
	@echo "  make nix-check   - Validate flake"
