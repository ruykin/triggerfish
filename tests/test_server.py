"""Tests for LSP server."""

import asyncio
from pathlib import Path

import pytest

from triggerfish.config import TriggerfishConfig
from triggerfish.server import TriggerfishLanguageServer


@pytest.mark.asyncio
async def test_index_file_adds_symbols(tmp_path) -> None:
    log_file = tmp_path / "log.txt"
    config = TriggerfishConfig(log_file=log_file)
    server = TriggerfishLanguageServer(config)
    server._workspace_root = tmp_path

    file_path = tmp_path / "main.py"
    file_path.write_text("def main():\n    pass\n")

    def fake_generate_tags(_file_path):
        return [
            {"name": "main", "kind": "function", "line": 1, "path": str(file_path)}
        ]

    server.ctags.generate_tags = fake_generate_tags
    await server._index_file(file_path)

    symbols = server.index.get_symbols()
    assert any(symbol.name == "main.py" for symbol in symbols)
    assert any(symbol.name == "main" for symbol in symbols)
