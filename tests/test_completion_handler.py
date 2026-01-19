"""Tests for completion handler."""

from pathlib import Path

from triggerfish.completion_handler import CompletionHandler
from triggerfish.config import TriggerfishConfig
from triggerfish.symbol_index import Symbol, SymbolIndex, SymbolKind


def test_should_trigger_and_parse() -> None:
    index = SymbolIndex()
    config = TriggerfishConfig(log_file=Path("/tmp/log.txt"))
    handler = CompletionHandler(index, config)

    line = "open @utils"
    assert handler.should_trigger(line, len(line))
    assert handler.parse_query(line, len(line)) == "utils"


def test_get_completions() -> None:
    index = SymbolIndex()
    index.add_symbols(
        [
            Symbol(name="utils.py", kind=SymbolKind.FILE, file_path=Path("/tmp/utils.py"), line=1),
            Symbol(name="main.py", kind=SymbolKind.FILE, file_path=Path("/tmp/main.py"), line=1),
        ]
    )
    config = TriggerfishConfig(log_file=Path("/tmp/log.txt"))
    handler = CompletionHandler(index, config)

    completions = handler.get_completions("@util", len("@util"))
    assert completions
    assert completions[0].label == "utils.py"
