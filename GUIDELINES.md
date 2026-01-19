# Triggerfish Development Guidelines

## Python Version
- Target Python 3.9+ for compatibility.

## Type Hints
- Required for all public functions and classes.
- Use `typing` module generics for 3.9 compatibility (`List`, `Dict`, `Optional`, `Union`).

Example:

```python
from typing import Dict, List, Optional

def func(items: List[str]) -> Optional[Dict[str, int]]:
    return None
```

## Docstrings
- Google-style docstrings for public APIs.

## Code Style
- Format with Black (line length 88).

## Linting
- Ruff: `E`, `F`, `W`, `I`, `N`, `UP` rules.
- Pylint: default configuration.
- Mypy: strict mode.

## Testing
- Pytest with >80% coverage.
- Use pytest-cov for reports.

## Error Handling
- Explicit exceptions only. Avoid bare `except:`.

## Logging
- Use the `logging` module; avoid `print()` in runtime code.

## Async/Await
- LSP handlers must be `async def`.

## Naming Conventions
- Classes: PascalCase.
- Functions/methods: snake_case.
- Constants: UPPER_SNAKE_CASE.
- Private members: leading underscore.
