from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from typing import TYPE_CHECKING, Literal

from langchain_core.messages import AIMessageChunk, HumanMessage
from pydantic import TypeAdapter, ValidationError

from core.constants import PIPELINE_TIMEOUT
from core.events import (
    DoneEvent,
    PipelineEvent,
    TextChunkEvent,
    ThinkingEvent,
    ToolCallEvent,
    ToolResultEvent,
)
from core.formatting import MAX_SUMMARY_LENGTH, extract_insights, summarize_args
from core.graph import build_pipeline_graph
from core.models.sources import DataSource, SourceRegistry
from core.models.turn import TurnState
from core.prompts import (
    AUTO_DASHBOARD,
    CARD_CONTEXT,
    DASHBOARD_SYSTEM,
    INSIGHT_SYSTEM,
    INSIGHT_USER,
)
from core.sandbox import SandboxManager
from core.state import CardSchema, DashboardCard, LoopResult, make_loop_result
from core.tools.context import ToolContext

if TYPE_CHECKING:
    from core.state import DataProfile

logger = logging.getLogger(__name__)
_card_adapter = TypeAdapter(CardSchema)


class Project:
    def __init__(
        self,
        project_id: str,
        model: str,
        api_key: str,
        sandbox_manager: SandboxManager,
    ) -> None:
        self.project_id = project_id
        self.model = model
        self.api_key = api_key
        self.sources = SourceRegistry()
        self.dashboard_cards: list[DashboardCard] | None = None

        self.sandbox = sandbox_manager
        self.op_lock = asyncio.Lock()
        self._source_count_at_last_build: int = 0
        self._last_insights: dict | None = None

    async def add_source(
        self,
        name: str,
        parquet_bytes: bytes,
        *,
        profile: DataProfile,
        row_count: int,
        columns: list[str],
        sample_text: str,
    ) -> DataSource:
        await self.sandbox.ensure_container(self.project_id)
        await self.sandbox.upload_source(self.project_id, name, parquet_bytes)

        source = DataSource(
            name=name, profile=profile, origin="csv",
            row_count=row_count, columns=columns, sample_text=sample_text,
        )
        self.sources.add(name, source)

        logger.info(
            "add_source '%s' (%d x %d) [project=%s]",
            name, row_count, len(columns), self.project_id,
        )
        return source

    async def remove_source(self, name: str) -> bool:
        if not self.sources.remove(name):
            return False
        try:
            await self.sandbox.remove_source(self.project_id, name)
        except Exception:
            logger.warning("Failed to remove source %s from sandbox (may be destroyed)", name)
        logger.info("remove_source '%s' [project=%s]", name, self.project_id)
        return True

    def needs_graph_rebuild(self) -> bool:
        return self.sources.count != self._source_count_at_last_build

    def mark_graph_built(self) -> None:
        self._source_count_at_last_build = self.sources.count

    async def run_pipeline(self, pipeline_type: Literal["insights", "dashboard"], turn: TurnState):
        async with self.op_lock:
            async for event in self._run_pipeline_inner(pipeline_type, turn):
                yield event

    async def _run_pipeline_inner(self, pipeline_type: Literal["insights", "dashboard"], turn: TurnState):
        if self.sources.is_empty:
            yield PipelineEvent(
                source=pipeline_type,
                event=DoneEvent(loop_result=LoopResult(
                    content="No data sources loaded.",
                    error="No sources",
                )),
            )
            return

        turn.reset()
        t0 = time.perf_counter()
        logger.info("%s pipeline started [project=%s]", pipeline_type, self.project_id)

        await self.sandbox.ensure_container(self.project_id)

        if pipeline_type == "insights":
            user_prompt, system_prompt = self._build_insights_prompt()
        else:
            user_prompt, system_prompt = self._build_dashboard_prompt()

        pipeline_graph = build_pipeline_graph(self.model, self.api_key, system_prompt)
        config = self._make_config(turn, pipeline_type, recursion_limit=12)
        content_parts = []

        try:
            async with asyncio.timeout(PIPELINE_TIMEOUT):
                async for event in self.stream_graph(
                    pipeline_graph,
                    {"messages": [HumanMessage(content=user_prompt)]},
                    config,
                ):
                    if isinstance(event, TextChunkEvent):
                        content_parts.append(event.chunk)
                    yield PipelineEvent(source=pipeline_type, event=event)

                loop_result = make_loop_result(content_parts, turn)

                if pipeline_type == "insights":
                    insights = extract_insights(loop_result)
                    yield PipelineEvent(
                        source=pipeline_type,
                        event=DoneEvent(loop_result=loop_result),
                    )
                    self._last_insights = insights
                else:
                    self._validate_cards(loop_result, turn)
                    yield PipelineEvent(
                        source=pipeline_type,
                        event=DoneEvent(loop_result=loop_result),
                    )
        except TimeoutError:
            logger.error("%s pipeline timed out [project=%s]", pipeline_type, self.project_id)
            yield PipelineEvent(
                source=pipeline_type,
                event=DoneEvent(loop_result=LoopResult(
                    content="The analysis took too long. Please try again.",
                    error="Pipeline timed out",
                )),
            )
        except Exception as exc:
            logger.error("%s pipeline failed [project=%s]", pipeline_type, self.project_id, exc_info=True)
            detail = str(exc).strip() or type(exc).__name__
            yield PipelineEvent(
                source=pipeline_type,
                event=DoneEvent(loop_result=LoopResult(
                    content=f"Something went wrong: {detail}",
                    error=detail,
                )),
            )
        finally:
            logger.info(
                "%s pipeline done [project=%s] (%.1fs)",
                pipeline_type, self.project_id, time.perf_counter() - t0,
            )

    def get_last_insights(self) -> dict | None:
        return self._last_insights

    def _build_insights_prompt(self) -> tuple[str, str]:
        user_prompt = INSIGHT_USER.format(
            source_context=self.sources.combined_context(),
        )
        return user_prompt, INSIGHT_SYSTEM

    def _build_dashboard_prompt(self) -> tuple[str, str]:
        user_prompt = AUTO_DASHBOARD.format(
            source_context=self.sources.combined_context(),
        )
        return user_prompt, DASHBOARD_SYSTEM

    def build_card_context(self, card_ids: list[str] | None) -> str | None:
        if not card_ids:
            return None
        cards = [c for c in (self.dashboard_cards or []) if c.id in card_ids]
        if not cards:
            return None
        details = []
        for c in cards:
            entry = f"- ID: {c.id}\n  Title: {c.title}\n  Type: {c.type}"
            if c.code:
                entry += f"\n  Code:\n```python\n{c.code}\n```"
            details.append(entry)
        return CARD_CONTEXT.format(card_details="\n\n".join(details))

    def _make_config(self, turn: TurnState, thread_suffix="pipeline", recursion_limit=None):
        config = {
            "configurable": {
                "thread_id": f"{self.project_id}-{thread_suffix}",
                "tool_context": ToolContext(
                    project_id=self.project_id,
                    sandbox=self.sandbox,
                    sources=self.sources,
                    turn=turn,
                    todos=[],
                ),
            }
        }
        if recursion_limit is not None:
            config["recursion_limit"] = recursion_limit
        return config

    async def stream_graph(self, graph, input_data, config):
        tool_call_t0 = None

        async for mode, chunk in graph.astream(
            input_data, config, stream_mode=["messages", "updates"]
        ):
            if mode == "messages":
                msg_chunk, _metadata = chunk
                if isinstance(msg_chunk, AIMessageChunk):
                    content = msg_chunk.content
                    if isinstance(content, str) and content:
                        yield TextChunkEvent(chunk=content)
                    elif isinstance(content, list):
                        for block in content:
                            if not isinstance(block, dict):
                                continue
                            if block.get("type") == "thinking":
                                yield ThinkingEvent(content=block.get("thinking", ""))
                            elif block.get("type") == "text":
                                yield TextChunkEvent(chunk=block.get("text", ""))
            elif mode == "updates":
                if "model" in chunk:
                    for msg in chunk["model"].get("messages", []):
                        if hasattr(msg, "tool_calls") and msg.tool_calls:
                            tool_call_t0 = time.perf_counter()
                            for tc in msg.tool_calls:
                                args_json = json.dumps(tc.get("args", {}))
                                summary = summarize_args(tc["name"], args_json)
                                yield ToolCallEvent(
                                    tool_name=tc["name"],
                                    arguments_summary=summary,
                                )
                elif "tools" in chunk:
                    elapsed = (
                        int((time.perf_counter() - tool_call_t0) * 1000) if tool_call_t0 else 0
                    )
                    for tmsg in chunk["tools"].get("messages", []):
                        content = tmsg.content if hasattr(tmsg, "content") else str(tmsg)
                        name = getattr(tmsg, "name", "unknown")
                        if name == "ask_question":
                            continue
                        success = getattr(tmsg, "status", "success") != "error"
                        yield ToolResultEvent(
                            tool_name=name,
                            success=success,
                            summary=str(content)[:MAX_SUMMARY_LENGTH],
                            duration_ms=elapsed,
                        )
                    tool_call_t0 = None

    def _validate_cards(self, loop_result: LoopResult, turn: TurnState) -> None:
        raw_cards = loop_result.cards
        if not raw_cards:
            return

        validated = []
        fig_idx = 0

        for raw in raw_cards:
            try:
                card_data = _card_adapter.validate_python(raw)
                card_fig = getattr(card_data, "fig", None)
                if (
                    card_data.type == "chart"
                    and card_fig is None
                    and fig_idx < len(loop_result.figs)
                ):
                    card_fig = loop_result.figs[fig_idx]
                    fig_idx += 1

                validated.append(
                    DashboardCard(
                        id=uuid.uuid4().hex[:8],
                        type=card_data.type,
                        title=card_data.title,
                        code=loop_result.code,
                        value=getattr(card_data, "value", None),
                        fig=card_fig,
                    )
                )
            except ValidationError as e:
                logger.warning("Skipped invalid card: %s", e)
        self.dashboard_cards = validated
