"""Client for Go core subprocess."""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
import threading
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional


@dataclass
class CoreConfig:
    """Configuration for core subprocess."""

    core_executable: str = "triggerfish-core"
    startup_timeout: float = 5.0
    request_timeout: float = 10.0
    enabled: bool = True


class CoreClient:
    """Manages Go core subprocess."""

    def __init__(self, config: CoreConfig) -> None:
        """Initialize core client."""
        self.config = config
        self._process: Optional[subprocess.Popen[str]] = None
        self._lock = threading.Lock()
        self._available = False

    def start(self) -> bool:
        """Start core subprocess.

        Returns:
            True if startup and health check succeed.
        """
        if not self.config.enabled:
            logging.info("Core subprocess disabled")
            return False

        try:
            core_path = self._find_core_binary()
            if not core_path:
                logging.warning("Core binary not found, running without core")
                return False

            self._process = subprocess.Popen(
                [str(core_path)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )

            if self._health_check():
                self._available = True
                logging.info("Core subprocess started successfully")
                return True

            self._stop()
            logging.warning("Core health check failed")
            return False

        except Exception as exc:
            logging.warning("Failed to start core subprocess: %s", exc)
            return False

    def stop(self) -> None:
        """Stop core subprocess."""
        self._stop()

    def _stop(self) -> None:
        if self._process:
            try:
                self._process.terminate()
                self._process.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                self._process.kill()
                self._process.wait()
            finally:
                self._process = None
                self._available = False

    def is_available(self) -> bool:
        """Check if core is available."""
        return self._available and self._process is not None

    def request(self, method: str, params: Dict[str, object]) -> Optional[Dict[str, object]]:
        """Send request to core.

        Args:
            method: Method name.
            params: Request parameters.

        Returns:
            Result dict on success, otherwise None.
        """
        if not self.is_available() or not self._process:
            return None

        with self._lock:
            try:
                request_id = str(uuid.uuid4())
                request = {
                    "id": request_id,
                    "method": method,
                    "params": params,
                }

                request_json = json.dumps(request) + "\n"
                assert self._process.stdin is not None
                self._process.stdin.write(request_json)
                self._process.stdin.flush()

                assert self._process.stdout is not None
                response_line = self._process.stdout.readline().strip()
                if not response_line:
                    logging.error("Core request timeout: %s", method)
                    return None

                response = json.loads(response_line)

                if response.get("id") != request_id:
                    logging.error("Response ID mismatch")
                    return None

                if "error" in response:
                    logging.error("Core error: %s", response["error"])
                    return None

                result = response.get("result")
                if isinstance(result, dict):
                    return result
                return None

            except Exception as exc:
                logging.error("Core communication error: %s", exc)
                return None

    def _health_check(self) -> bool:
        """Perform health check."""
        result = self.request("health", {})
        return result is not None and result.get("status") == "ok"

    def _find_core_binary(self) -> Optional[Path]:
        """Find core binary."""
        workspace_core = (
            Path(__file__).parent.parent.parent / "core" / "triggerfish-core"
        )
        if workspace_core.exists():
            return workspace_core

        core_in_path = shutil.which(self.config.core_executable)
        if core_in_path:
            return Path(core_in_path)

        return None
