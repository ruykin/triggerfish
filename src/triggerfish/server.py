"""LSP server implementation."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from lsprotocol.types import (
    CompletionList,
    CompletionOptions,
    CompletionParams,
    DidChangeTextDocumentParams,
    DidOpenTextDocumentParams,
    InitializeParams,
    InitializeResult,
    ServerCapabilities,
    TextDocumentSyncKind,
)
from pygls.server import LanguageServer
from pygls.uris import uri_to_path

from .completion_handler import CompletionHandler
from .config import TriggerfishConfig
from .ctags_manager import CTagsError, CTagsManager
from .symbol_index import Symbol, SymbolIndex, SymbolKind


_KIND_MAP: Dict[str, SymbolKind] = {
    "class": SymbolKind.CLASS,
    "function": SymbolKind.FUNCTION,
    "method": SymbolKind.METHOD,
    "member": SymbolKind.VARIABLE,
    "variable": SymbolKind.VARIABLE,
}


class TriggerfishLanguageServer(LanguageServer):
    """Language Server for Triggerfish."""

    def __init__(self, config: TriggerfishConfig) -> None:
        super().__init__("triggerfish", "0.1.0")
        self.config = config
        self.ctags = CTagsManager(config)
        self.index = SymbolIndex()
        self.completion = CompletionHandler(self.index, config)
        self._workspace_root: Optional[Path] = None
        self._setup_logging()
        self._register_handlers()

    def _setup_logging(self) -> None:
        logging.basicConfig(
            filename=str(self.config.log_file),
            level=getattr(logging, self.config.log_level.upper(), logging.INFO),
            format="%(asctime)s %(levelname)s %(message)s",
        )

    def _register_handlers(self) -> None:
        @self.feature("initialize")
        async def initialize(params: InitializeParams) -> InitializeResult:
            self._workspace_root = _get_workspace_root(params)
            if self._workspace_root:
                await self._index_workspace(self._workspace_root)
            capabilities = ServerCapabilities(
                text_document_sync=TextDocumentSyncKind.Incremental,
                completion_provider=CompletionOptions(
                    trigger_characters=[CompletionHandler.FILE_TRIGGER]
                ),
            )
            return InitializeResult(capabilities=capabilities)

        @self.feature("initialized")
        async def initialized(_params) -> None:
            logging.info("Triggerfish LSP initialized")

        @self.feature("textDocument/didOpen")
        async def did_open(params: DidOpenTextDocumentParams) -> None:
            file_path = Path(uri_to_path(params.text_document.uri))
            await self._index_file(file_path)

        @self.feature("textDocument/didChange")
        async def did_change(params: DidChangeTextDocumentParams) -> None:
            file_path = Path(uri_to_path(params.text_document.uri))
            await self._index_file(file_path)

        @self.feature("textDocument/completion")
        async def completion(params: CompletionParams) -> CompletionList:
            document = self.workspace.get_document(params.text_document.uri)
            line_text = ""
            if params.position.line < len(document.lines):
                line_text = document.lines[params.position.line]
            items = self.completion.get_completions(
                line_text, params.position.character
            )
            return CompletionList(is_incomplete=False, items=items)

    async def _index_file(self, file_path: Path) -> None:
        try:
            tags = self.ctags.generate_tags(file_path)
        except CTagsError as exc:
            logging.warning("ctags failed for %s: %s", file_path, exc)
            tags = []

        symbols = list(self._symbols_from_tags(file_path, tags))
        self.index.update_file(file_path, symbols)

    async def _index_workspace(self, workspace_path: Path) -> None:
        for file_path in workspace_path.rglob("*.py"):
            if file_path.is_file():
                await self._index_file(file_path)
        logging.info("Indexed workspace: %s", self.index.stats())

    def _symbols_from_tags(
        self, file_path: Path, tags: Iterable[Dict[str, object]]
    ) -> Iterable[Symbol]:
        file_symbol_name = _relative_name(self._workspace_root, file_path)
        yield Symbol(
            name=file_symbol_name,
            kind=SymbolKind.FILE,
            file_path=file_path,
            line=1,
        )
        for tag in tags:
            kind_name = tag.get("kind")
            if not isinstance(kind_name, str):
                continue
            symbol_kind = _KIND_MAP.get(kind_name)
            if symbol_kind is None:
                continue
            name = tag.get("name")
            if not isinstance(name, str):
                continue
            line = tag.get("line")
            if not isinstance(line, int):
                line = 1
            scope = tag.get("scope")
            if scope is not None and not isinstance(scope, str):
                scope = None
            language = tag.get("language")
            if language is not None and not isinstance(language, str):
                language = None
            yield Symbol(
                name=name,
                kind=symbol_kind,
                file_path=file_path,
                line=line,
                scope=scope,
                language=language,
            )


def create_server(config: Optional[TriggerfishConfig] = None) -> TriggerfishLanguageServer:
    """Create a Triggerfish language server."""
    if config is None:
        config = TriggerfishConfig.from_env()
    return TriggerfishLanguageServer(config)


def _get_workspace_root(params: InitializeParams) -> Optional[Path]:
    if params.workspace_folders:
        folder = params.workspace_folders[0]
        return Path(uri_to_path(folder.uri))
    if params.root_uri:
        return Path(uri_to_path(params.root_uri))
    return None


def _relative_name(workspace_root: Optional[Path], file_path: Path) -> str:
    if workspace_root:
        try:
            return file_path.relative_to(workspace_root).as_posix()
        except ValueError:
            pass
    return file_path.name
