"""IPython-based execution kernel for the sandbox container."""


import contextlib
import ctypes
import io
import json
import logging
import threading
import time
import traceback
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from IPython.core.interactiveshell import InteractiveShell

logger = logging.getLogger(__name__)


class _ExecutionTimeout(Exception):
    pass


def _sanitize(obj: Any) -> Any:
    """Recursively convert non-JSON-serializable types to plain Python."""
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitize(v) for v in obj]
    if hasattr(obj, "to_json"):  # Plotly Figure / BaseFigure
        return json.loads(obj.to_json())
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    return obj


@dataclass
class ExecutionResult:
    stdout: str = ""
    stderr: str = ""
    figures: list[dict] = field(default_factory=list)
    result: dict | list | str | int | float | bool | None = None
    cards: list[dict] = field(default_factory=list)
    card_updates: dict[str, dict] = field(default_factory=dict)
    error: str | None = None
    duration_ms: float = 0.0


class SandboxKernel:
    _shell: Any

    def __init__(self) -> None:
        self._shell = InteractiveShell.instance()
        self._shell.colors = "NoColor"
        self._setup()
        self._autoload_sources()

    def _setup(self) -> None:
        ns = self._shell.user_ns
        ns["pd"] = pd
        ns["px"] = px
        ns["go"] = go
        ns["np"] = np
        import re

        ns["re"] = re

    def _autoload_sources(self) -> None:
        """Load all .parquet files from /data/sources/ into the namespace."""
        from pathlib import Path

        sources_dir = Path("/data/sources")
        if not sources_dir.exists():
            return
        for parquet_path in sorted(sources_dir.glob("*.parquet")):
            name = parquet_path.stem
            try:
                df = pd.read_parquet(parquet_path)
                self._shell.user_ns[name] = df
            except Exception:
                logger.warning("Failed to load %s", parquet_path)

    def execute(self, code: str, timeout_seconds: float = 30.0) -> ExecutionResult:
        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()

        start = time.perf_counter()
        error: str | None = None
        timed_out = False

        exec_result_holder: list = []
        exec_error_holder: list = []

        def _run():
            try:
                with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
                    res = self._shell.run_cell(code, silent=True, store_history=False)
                exec_result_holder.append(res)
            except _ExecutionTimeout:
                exec_error_holder.append("timeout")
            except Exception:
                exec_error_holder.append(traceback.format_exc())

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
        thread.join(timeout=timeout_seconds)

        if thread.is_alive():
            # Thread is still running — try to interrupt it
            timed_out = True
            with contextlib.suppress(Exception):
                ctypes.pythonapi.PyThreadState_SetAsyncExc(
                    ctypes.c_ulong(thread.ident or 0),
                    ctypes.py_object(_ExecutionTimeout),
                )
            thread.join(timeout=2)
            error = f"Execution timed out after {timeout_seconds:.0f}s"
        elif exec_error_holder:
            err = exec_error_holder[0]
            error = f"Execution timed out after {timeout_seconds:.0f}s" if err == "timeout" else err
        elif exec_result_holder:
            exec_result = exec_result_holder[0]
            if exec_result.error_in_exec is not None:
                error = "".join(
                    traceback.format_exception(
                        type(exec_result.error_in_exec),
                        exec_result.error_in_exec,
                        exec_result.error_in_exec.__traceback__,
                    )
                )
            elif exec_result.error_before_exec is not None:
                error = "".join(
                    traceback.format_exception(
                        type(exec_result.error_before_exec),
                        exec_result.error_before_exec,
                        exec_result.error_before_exec.__traceback__,
                    )
                )

        duration_ms = (time.perf_counter() - start) * 1000

        figures: list[dict] = []
        result = None
        cards: list[dict] = []
        card_updates: dict[str, dict] = {}

        if not timed_out:
            try:
                figures = self._extract_figures()
            except Exception as exc:
                stderr_buf.write(f"\n[sandbox] Failed to extract figures: {exc}\n")
                if error is None:
                    error = f"Figure extraction failed: {exc}"

            try:
                result = self._extract_result()
            except Exception as exc:
                stderr_buf.write(f"\n[sandbox] Failed to extract result: {exc}\n")
                if error is None:
                    error = f"Result extraction failed: {exc}"

            try:
                cards = self._extract_cards()
            except Exception as exc:
                stderr_buf.write(f"\n[sandbox] Failed to extract cards: {exc}\n")
                if error is None:
                    error = f"Card extraction failed: {exc}"

            try:
                card_updates = self._extract_card_updates()
            except Exception as exc:
                stderr_buf.write(f"\n[sandbox] Failed to extract card_updates: {exc}\n")
                if error is None:
                    error = f"Card updates extraction failed: {exc}"

        return ExecutionResult(
            stdout=stdout_buf.getvalue(),
            stderr=stderr_buf.getvalue(),
            figures=figures,
            result=result,
            cards=cards,
            card_updates=card_updates,
            error=error,
            duration_ms=duration_ms,
        )

    def inject_dataframe(self, name: str, parquet_bytes: bytes) -> tuple[int, list[str]]:
        buf = io.BytesIO(parquet_bytes)
        df = pd.read_parquet(buf)
        self._shell.user_ns[name] = df
        return len(df), list(df.columns)

    def remove_dataframe(self, name: str) -> bool:
        ns = self._shell.user_ns
        if name in ns:
            del ns[name]
            return True
        return False

    def list_dataframes(self) -> list[str]:
        ns = self._shell.user_ns
        return [k for k, v in ns.items() if isinstance(v, pd.DataFrame)]

    def _extract_figures(self) -> list[dict]:
        ns = self._shell.user_ns
        figs: list[dict] = []
        fig = ns.pop("fig", None)
        if fig is not None:
            items = fig if isinstance(fig, list) else [fig]
            for f in items:
                if hasattr(f, "to_json"):
                    figs.append(_sanitize(f))
        return figs

    def _extract_result(self) -> dict | list | str | int | float | bool | None:
        ns = self._shell.user_ns
        result = ns.pop("result", None)
        if result is None:
            return None
        if isinstance(result, pd.DataFrame):
            return _sanitize(result.to_dict(orient="records"))
        if isinstance(result, pd.Series):
            return _sanitize(result.to_dict())
        if isinstance(result, (dict, list)):
            return _sanitize(result)
        if isinstance(result, (str, int, float, bool)):
            return result
        if isinstance(result, (np.integer, np.floating, np.bool_)):
            return _sanitize(result)
        return str(result)

    def _extract_cards(self) -> list[dict]:
        ns = self._shell.user_ns
        cards = ns.pop("cards", None)
        if cards is None:
            return []
        if not isinstance(cards, list):
            return []
        return [_sanitize(c) for c in cards if isinstance(c, dict)]

    def _extract_card_updates(self) -> dict[str, dict]:
        ns = self._shell.user_ns
        raw = ns.pop("card_updates", None)
        if raw is None or not isinstance(raw, dict):
            return {}
        sanitized = {}
        for card_id, fig in raw.items():
            if hasattr(fig, "to_json"):
                sanitized[str(card_id)] = _sanitize(fig)
        return sanitized
