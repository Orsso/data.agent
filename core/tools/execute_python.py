import json
import logging
import time

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from core.constants import RESULT_DICT_MAX_CHARS, RESULT_OTHER_MAX_CHARS, STDOUT_MAX_CHARS
from core.sandbox.exceptions import SandboxError, SandboxTimeoutError
from core.tools.context import get_tool_context
from core.tools.exceptions import CodeExecutionError, ToolError

logger = logging.getLogger(__name__)


@tool
async def execute_python(code: str, config: RunnableConfig) -> str:
    """Execute Python code in an isolated sandbox container.

    OUTPUT SLOTS (consumed after each call — only these are captured):
    - `fig`    → ONE Plotly Figure displayed in the chat. One chart per call.
    - `result` → Data returned to you (dict, list, scalar). Use for inspection or intermediate values.
    - `cards`  → Dashboard card list.
    - `card_updates` → Dict mapping card IDs to new Plotly figures. MANDATORY when modifying selected dashboard cards. Using `fig` when cards are selected creates a new chart instead of updating the card.
    Any other variable name (fig1, my_chart, etc.) is IGNORED for display. NEVER call fig.show().

    ENVIRONMENT:
    - Pre-injected: pd, px (plotly.express), go (plotly.graph_objects), np, re.
    - All uploaded DataFrames are available by name (e.g. `df`, `sales`, `users`).
    - Variables persist between calls (except output slots, which are consumed).
    - Imports ARE allowed (sandbox is isolated).

    DATA RULES:
    - Clean columns before numeric ops: df['col'].str.replace('[₹$€,]', '', regex=True).astype(float)
    - Handle NaN: dropna() before aggregation, fillna() before plotting.
    - >20 categories: show top N with .nlargest()/.head().
    - >1000 rows: aggregate before plotting. Never scatter-plot raw data.
    - Inspect data (describe, value_counts) before charting when unsure about values or distributions.
    """
    ctx = get_tool_context(config)

    if not code.strip():
        raise ToolError("Error: Empty code block.")

    code_preview = code.replace("\n", "\\n")[:200]
    logger.info("execute_python [project=%s]: %s", ctx.project_id, code_preview)
    t0 = time.perf_counter()

    try:
        # Ensure container exists (lazy creation)
        await ctx.sandbox.ensure_container(ctx.project_id)
        response = await ctx.sandbox.execute(ctx.project_id, code)
    except SandboxTimeoutError as exc:
        logger.warning("execute_python timeout [project=%s]", ctx.project_id)
        raise ToolError(
            "Error: Code execution timed out (60s limit). Simplify your code or process less data."
        ) from exc
    except SandboxError as exc:
        logger.warning("execute_python sandbox error [project=%s]: %s", ctx.project_id, exc)
        raise ToolError(f"Error: Sandbox unavailable — {exc}") from exc

    # Update turn state with sandbox response
    figs = response.get("figures", [])
    cards = response.get("cards", [])
    card_updates = response.get("card_updates", {})
    result = response.get("result")
    stdout = response.get("stdout", "")

    if figs:
        ctx.turn.figs.extend(figs)
    if cards:
        ctx.turn.cards.extend(cards)
    if card_updates:
        ctx.turn.card_updates.update(card_updates)
    ctx.turn.code = code
    if result is not None:
        ctx.turn.result = result

    elapsed_ms = int((time.perf_counter() - t0) * 1000)

    error = response.get("error")
    if error:
        logger.warning(
            "execute_python error [project=%s] (%dms): %s", ctx.project_id, elapsed_ms, error
        )
        source_names = list(ctx.sources.get_all().keys())
        parts = [f"Error: {error}"]
        if figs:
            parts.append(
                f"Note: {len(figs)} figure(s) were captured before the error. "
                f"Total figures this turn: {len(ctx.turn.figs)}. Do NOT regenerate them."
            )
        parts.append(f"Available DataFrames: {source_names}")
        raise CodeExecutionError("\n".join(parts))

    logger.info(
        "execute_python result: %d new figs (%d total), %d new cards (%d total), %d card_updates (%dms)",
        len(figs),
        len(ctx.turn.figs),
        len(cards),
        len(ctx.turn.cards),
        len(card_updates),
        elapsed_ms,
    )
    if not figs and stdout:
        logger.debug("execute_python stdout (no figs): %.300s", stdout.strip())
    # Warn if fig was used but cards were selected for modification
    if figs and ctx.turn.selected_card_ids and not card_updates:
        warning = (
            "\n\n⚠️ WARNING: You used `fig` but dashboard cards are selected for modification. "
            "The user wants to UPDATE existing cards, not create new charts. "
            'Use `card_updates = {"<card_id>": fig}` instead of `fig = ...`. '
            "Re-run the code with `card_updates`."
        )
        return (
            _format_output(result, figs, cards, card_updates, stdout, total_figs=len(ctx.turn.figs))
            + warning
        )

    return _format_output(result, figs, cards, card_updates, stdout, total_figs=len(ctx.turn.figs))


def _format_output(result, figs, cards, card_updates, stdout, total_figs=0) -> str:
    parts = []

    if len(figs) > 1:
        parts.append(f"[{len(figs)} charts generated]")
    elif figs:
        parts.append("[Chart generated]")
    if total_figs > len(figs):
        parts.append(f"[{total_figs} charts total this turn]")

    if isinstance(result, list) and result and isinstance(result[0], dict):
        # DataFrame converted to records
        parts.append(
            f"Returned {len(result)} rows.\n"
            f"Sample:\n{json.dumps(result[:3], ensure_ascii=False, default=str)}"
        )
    elif isinstance(result, dict):
        parts.append(json.dumps(result, ensure_ascii=False, default=str)[:RESULT_DICT_MAX_CHARS])
    elif result is not None:
        parts.append(str(result)[:RESULT_OTHER_MAX_CHARS])
    elif card_updates:
        parts.append(f"[{len(card_updates)} card update(s) proposed]")
    elif cards:
        parts.append(f"[{len(cards)} cards generated]")
    elif stdout.strip():
        parts.append(stdout.strip()[:STDOUT_MAX_CHARS])
    elif not figs:
        parts.append("Code executed with no output.")

    return "\n".join(parts)
