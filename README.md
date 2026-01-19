# Triggerfish LSP

Lightning-fast LSP server powered by universal-ctags with smart trigger-based completions.

## Features

- `@` trigger for file completions with fuzzy search
- Powered by universal-ctags for language-agnostic indexing
- Works with Python, JavaScript, TypeScript, and any ctags-supported language

## Requirements

- Python 3.9+
- universal-ctags

### Installing universal-ctags

Refer to the universal-ctags install docs for your OS:
https://github.com/universal-ctags/ctags

## Installation

```bash
# From source
pip install -e .

# From PyPI (future)
pip install triggerfish-lsp
```

## Usage

```bash
# Start server
python -m triggerfish

# With debug logging
python -m triggerfish --log-level DEBUG
```

## Editor Configuration

### Generic LSP Client

- Command: `python -m triggerfish`
- Trigger character: `@`

### VSCode

Example `settings.json` snippet:

```json
{
  "triggerfish.command": "python",
  "triggerfish.args": ["-m", "triggerfish"],
  "triggerfish.triggerCharacters": ["@"]
}
```

### Neovim (nvim-lspconfig)

```lua
require('lspconfig').triggerfish.setup{
  cmd = { 'python', '-m', 'triggerfish' },
  filetypes = { 'python', 'javascript', 'typescript' },
}
```

## Example

```
# In any file, type:
@myfi

# Shows completions:
# - my_file.py
# - my_first.js
# - my_filter.ts
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Check coverage
pytest --cov=src/triggerfish --cov-report=html

# Format code
black src/ tests/

# Type check
mypy src/

# Lint
ruff check src/ tests/
pylint src/
```

## Troubleshooting

- Logs location: `~/.triggerfish/logs/triggerfish.log`
- Common issues: ctags not found, no completions appearing

## License

Apache 2.0
