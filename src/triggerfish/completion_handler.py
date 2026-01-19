"""Completion logic for Triggerfish."""

from __future__ import annotations

from typing import List, Optional

from lsprotocol.types import CompletionItem, CompletionItemKind

from .config import TriggerfishConfig
from .symbol_index import Symbol, SymbolIndex, SymbolKind


class CompletionHandler:
    """Handles @ trigger completion requests."""

    FILE_TRIGGER = "@"

    def __init__(self, symbol_index: SymbolIndex, config: TriggerfishConfig) -> None:
        self._index = symbol_index
        self._config = config

    def should_trigger(self, line: str, character: int) -> bool:
        return line.rfind(self.FILE_TRIGGER, 0, character) != -1

    def parse_query(self, line: str, character: int) -> Optional[str]:
        trigger_index = line.rfind(self.FILE_TRIGGER, 0, character)
        if trigger_index == -1:
            return None
        query = line[trigger_index + 1 : character]
        if not query:
            return ""
        if any(char.isspace() for char in query):
            return None
        return query

    def get_completions(self, line: str, character: int) -> List[CompletionItem]:
        query = self.parse_query(line, character)
        if query is None:
            return []

        if query == "":
            symbols = self._index.get_symbols(SymbolKind.FILE)
            matches = [(symbol, 0.0) for symbol in symbols[: self._config.max_completion_items]]
        else:
            matches = self._index.fuzzy_search(
                query,
                kind=SymbolKind.FILE,
                limit=self._config.max_completion_items,
                min_score=self._config.min_fuzzy_score,
            )

        return [self._to_completion_item(symbol, score) for symbol, score in matches]

    def _to_completion_item(self, symbol: Symbol, score: float) -> CompletionItem:
        sort_text = f"{100 - int(score):03d}"
        return CompletionItem(
            label=symbol.name,
            kind=CompletionItemKind.File,
            detail=f"file at {symbol.file_path}:{symbol.line}",
            sort_text=sort_text,
            insert_text=symbol.name,
        )
