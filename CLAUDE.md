# Triggerfish LSP - Developer Guide

This document provides implementation details and architecture overview for developers working on Triggerfish LSP.

## Architecture Overview

### Core Components

```
┌──────────────────────────────────────────────────────────┐
│                    LSP Client (Editor)                    │
│              (VSCode, Neovim, Zed, etc.)                  │
└────────────────────────┬─────────────────────────────────┘
                         │ LSP Protocol (stdio)
┌────────────────────────▼─────────────────────────────────┐
│        TriggerfishLanguageServer (server.py)             │
│  • Handles LSP protocol events                           │
│  • Manages workspace indexing                            │
│  • Routes completion requests                            │
└────────────────┬──────────────────────┬──────────────────┘
                 │                      │
      ┌──────────▼─────────┐    ┌──────▼──────────────┐
      │  SymbolIndex       │    │ CompletionHandler   │
      │  (symbol_index.py) │    │ (completion_handler)│
      │                    │    │                     │
      │ • add_symbols()    │    │ • should_trigger()  │
      │ • fuzzy_search()   │    │ • parse_query()     │
      │ • get_symbols()    │    │ • get_completions() │
      └────────────────────┘    └──────────────────────┘
             ▲                            │
             │                            │
      ┌──────┴────────────────────────────┘
      │
      │   CTagsManager (ctags_manager.py)
      │   • Calls universal-ctags
      │   • Parses JSON output
      └───────────────────────────────────────┘
                 │
                 │ Optional (STDIO JSON)
                 ▼
      ┌───────────────────────────────────────┐
      │         Go Core Subprocess            │
      │     (core/cmd/triggerfish-core)       │
      │ • Graph storage and queries           │
      │ • health, index_file, find_symbol     │
      └───────────────────────────────────────┘
```

## File Structure

```
lsp/
├── triggerfish/
│   ├── __init__.py
│   ├── __main__.py
│   ├── server.py
│   ├── completion_handler.py
│   ├── symbol_index.py
│   ├── ctags_manager.py
│   ├── config.py
│   └── core_client.py
├── tests/
│   ├── test_server.py
│   ├── test_completion_handler.py
│   ├── test_symbol_index.py
│   ├── test_ctags_manager.py
│   ├── test_config.py
│   ├── test_integration.py
│   └── test_multi_trigger.py
└── pyproject.toml

core/
├── cmd/triggerfish-core/main.go
└── internal/
    ├── graph/
    └── server/

.vscode/extensions/triggerfish-lsp/
├── extension.js
├── package.json
└── package-lock.json
```

## Key Implementation Details

### 1. CompletionHandler (completion_handler.py)

Generic handler that supports multiple triggers and symbol kinds:

```python
handler = CompletionHandler(
    index=symbol_index,
    config=config,
    trigger="@",
    symbol_kinds=[SymbolKind.FILE],
    completion_kind=CompletionItemKind.File
)
```

**Features:**
- Parses query text after trigger character
- Rejects queries with whitespace
- Fuzzy search using `rapidfuzz.WRatio`
- Returns sorted completions by score

### 2. SymbolIndex (symbol_index.py)

In-memory index with three data structures for fast lookup:

```python
self._symbols: List[Symbol]
self._by_file: Dict[Path, List[Symbol]]
self._by_kind: Dict[SymbolKind, List[Symbol]]
```

**Symbol Types:**
- `FILE`: File paths (for `@` trigger)
- `CLASS`: Class definitions (for `.` trigger)
- `METHOD`: Class methods (for `#` trigger)
- `FUNCTION`: Standalone functions (for `#` trigger)
- `VARIABLE`: Variables (not currently used)

### 3. CTags Integration (server.py)

**Symbol Parsing Flow:**

1. During workspace initialization, iterate all project files
2. For each file, call `_parse_code_symbols(file_path)`
3. Execute `ctags --output-format=json` on the file
4. Parse JSON output and map kinds to `SymbolKind`
5. Add symbols to the index

### 4. Go Core Subprocess (core/)

- Optional subprocess (STDIO, newline-delimited JSON)
- Health check on LSP startup
- Handles `health`, `index_file`, `find_symbol`, `neighbors`
- Current graph v0 stores file nodes only

## Adding a New Trigger

To add a new trigger (e.g., `$` for variables):

1. **Create handler** in `server.py.__init__()`:
```python
self.variable_completion = CompletionHandler(
    self.index, config, "$",
    [SymbolKind.VARIABLE],
    CompletionItemKind.Variable
)
```

2. **Register trigger** in `_register_handlers()`:
```python
completion_provider=CompletionOptions(
    trigger_characters=["@", ".", "#", "$"]
)
```

3. **Add to routing** in `_completion()`:
```python
handlers = [
    self.file_completion,
    self.class_completion,
    self.method_completion,
    self.variable_completion,
]
```

4. **Update ctags mapping** in `_map_ctags_kind()`:
```python
"variable": SymbolKind.VARIABLE,
"var": SymbolKind.VARIABLE,
```

## Extending File Type Support

Currently restricted to `.txt` files at `server.py`:

```python
if not params.text_document.uri.endswith(".txt"):
    return CompletionList(is_incomplete=False, items=[])
```

To enable in code files:

**Option A - Remove restriction entirely:**
```python
# Delete the check, allow all filetypes
```

**Option B - Whitelist specific extensions:**
```python
ALLOWED_EXTENSIONS = {".txt", ".md", ".rst", ".org"}
ext = Path(params.text_document.uri).suffix
if ext not in ALLOWED_EXTENSIONS:
    return CompletionList(is_incomplete=False, items=[])
```

**Option C - Different triggers per filetype:**
```python
if uri.endswith(".txt"):
    handlers = [file, class, method]
elif uri.endswith((".py", ".js", ".ts")):
    handlers = [class, method]
else:
    return CompletionList(is_incomplete=False, items=[])
```

## Development Workflow

### Running in Development

```bash
# Enter dev environment
nix develop

# Install in editable mode
pip install -e lsp[dev]

# Run with debug logging
cd lsp
python -m triggerfish --log-level DEBUG

# Watch logs
tail -f ~/.triggerfish/logs/triggerfish.log
```

### Testing Changes

```bash
# Run all tests
cd lsp
pytest tests/ -v

# Run with coverage
pytest --cov=triggerfish --cov-report=term
```

### Code Quality

```bash
# Format code
black lsp/triggerfish lsp/tests

# Type check
mypy lsp/triggerfish

# Lint
ruff check lsp/triggerfish lsp/tests
```

## VSCode Extension

The project includes a complete VSCode extension at `.vscode/extensions/triggerfish-lsp/`.

### Python Path Resolution

```javascript
const workspaceFolder = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
const defaultPythonPath = workspaceFolder
  ? `${workspaceFolder}/lsp/.venv/bin/python`
  : 'python';
const pythonPath = config.get('pythonPath') || defaultPythonPath;
```

## Common Pitfalls

### 1. CTags Not Found

**Symptom:** No class/method completions
**Solution:**
- Install `universal-ctags` (not `exuberant-ctags`)
- Verify: `ctags --version` should show "Universal Ctags"

### 2. Trigger Not Working

**Symptom:** Completions don't appear
**Solution:**
- Check trigger is registered in `completion_provider`
- Verify handler is added to routing list
- Check logs for trigger detection

### 3. Wrong Symbols Returned

**Symptom:** Method completions show classes
**Solution:**
- Check `symbol_kinds` parameter in handler creation
- Verify ctags kind mapping in `_map_ctags_kind()`

## License

Apache 2.0
