{
  description = "Triggerfish LSP with Go core";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

        pythonEnv = pkgs.python313.withPackages (ps: with ps; [
          pip setuptools wheel
          pytest pytest-cov pytest-asyncio pytest-mock
          black mypy pylint
          pygls rapidfuzz python-dotenv
        ]);

      in {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            pythonEnv
            go_1_22 gopls gotools
            universal-ctags git gnumake
            nodejs_20 nodePackages.npm
          ];

          shellHook = ''
            echo "Triggerfish Development Environment"
            echo "Python: $(python --version)"
            echo "Go: $(go version)"
            echo ""

            if [ ! -d lsp/.venv ]; then
              python -m venv lsp/.venv
            fi
            source lsp/.venv/bin/activate

            if [ ! -f lsp/.venv/.installed ]; then
              pip install --upgrade pip > /dev/null 2>&1
              pip install -e lsp/[dev] > /dev/null 2>&1
              touch lsp/.venv/.installed
            fi

            echo "Run 'make help' for available commands"
          '';
        };
      }
    );
}
