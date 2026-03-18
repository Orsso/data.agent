import logging
import time
import uuid

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.types import Command

from core.events import (
    AskQuestionEvent,
    CardProposalsEvent,
    ChatRenamedEvent,
    DoneEvent,
    TextChunkEvent,
    ThinkingEvent,
    TodoUpdateEvent,
    ToolCallEvent,
    ToolResultEvent,
)
from core.graph import build_chat_graph, make_llm
from core.models.chat import ChatState
from core.models.turn import TurnState
from core.project import Project
from core.prompts import DATA_QUERY, build_chat_system
from core.state import (
    Answer,
    CardProposal,
    ChatMessage,
    Choice,
    LoopResult,
    Question,
    TodoItem,
    ToolStep,
    make_loop_result,
)
from core.tools.context import ToolContext

logger = logging.getLogger(__name__)


class ChatThread:
    def __init__(
        self,
        chat_id: str,
        project: Project,
        checkpointer: AsyncPostgresSaver | None,
    ) -> None:
        self.chat_id = chat_id
        self._project = project
        self._checkpointer = checkpointer
        self.chat = ChatState()
        self.turn = TurnState()
        self._pending_title: str | None = None

        self._graph = self._build_graph()

    def consume_pending_title(self) -> str | None:
        title = self._pending_title
        self._pending_title = None
        return title

    def _build_graph(self):
        p = self._project
        has_sources = not p.sources.is_empty
        source_count = p.sources.count
        system_prompt = build_chat_system(has_sources=has_sources, source_count=source_count)
        p.mark_graph_built()
        return build_chat_graph(p.model, p.api_key, self._checkpointer, system_prompt=system_prompt)

    def _ensure_graph_fresh(self):
        if self._project.needs_graph_rebuild():
            self._graph = self._build_graph()

    def _make_config(self):
        return {
            "configurable": {
                "thread_id": self.chat_id,
                "tool_context": ToolContext(
                    project_id=self._project.project_id,
                    sandbox=self._project.sandbox,
                    sources=self._project.sources,
                    turn=self.turn,
                    todos=self.chat.todos,
                ),
            }
        }

    async def run_chat(self, query: str, selected_card_ids: list[str] | None = None):
        lock = self._project.op_lock
        if lock.locked():
            yield DoneEvent(
                loop_result=LoopResult(
                    content="Another operation is in progress. Please wait.",
                    error="Concurrent operation",
                ),
                msg_id=uuid.uuid4().hex[:8],
            )
            return

        async with lock:
            async for event in self._run_chat_inner(query, selected_card_ids):
                yield event

    async def _run_chat_inner(self, query: str, selected_card_ids: list[str] | None = None):
        self.chat.todos = []
        self.turn.reset()
        self.turn.selected_card_ids = selected_card_ids or []
        self.chat.selected_card_ids = selected_card_ids or []
        self._ensure_graph_fresh()

        self.chat.messages.append(
            ChatMessage(role="user", content=query, msg_id=uuid.uuid4().hex[:8])
        )

        card_ctx = self._project.build_card_context(selected_card_ids)
        user_content = self._build_user_message(query, card_ctx)
        msg_id = uuid.uuid4().hex[:8]

        async for event in self._stream_and_finalize(
            {"messages": [HumanMessage(content=user_content)]},
            msg_id,
            selected_card_ids=selected_card_ids,
            auto_name_query=query,
        ):
            yield event

    async def resume_chat(self, answers: list[Answer]):
        async with self._project.op_lock:
            async for event in self._resume_chat_inner(answers):
                yield event

    async def _resume_chat_inner(self, answers: list[Answer]):
        self.turn.reset()
        self.turn.selected_card_ids = self.chat.selected_card_ids
        self.chat.pending_questions = None
        self.chat.pending_msg_id = None
        msg_id = uuid.uuid4().hex[:8]

        answer_map = {a.question: a.answer for a in answers}
        last_msg = self.chat.messages[-1] if self.chat.messages else None
        if last_msg and last_msg.asked_questions:
            for q in last_msg.asked_questions:
                if q.question in answer_map:
                    q.selected_answer = answer_map[q.question]

        resume_value = {"answers": [{"question": a.question, "answer": a.answer} for a in answers]}
        async for event in self._stream_and_finalize(
            Command(resume=resume_value),
            msg_id,
            selected_card_ids=self.chat.selected_card_ids,
        ):
            yield event

    async def _stream_and_finalize(
        self,
        graph_input,
        msg_id: str,
        *,
        selected_card_ids: list[str] | None = None,
        auto_name_query: str | None = None,
    ):
        t0 = time.perf_counter()
        config = self._make_config()

        content_parts = []
        tool_steps = []
        thinking_parts = []

        try:
            async for event in self._project.stream_graph(
                self._graph,
                graph_input,
                config,
            ):
                self._accumulate(event, content_parts, tool_steps, thinking_parts)
                yield event
                if isinstance(event, ToolResultEvent) and event.tool_name == "todo":
                    yield self._make_todo_event()

            state = await self._graph.aget_state(config)  # type: ignore[arg-type]
            if state.next:
                questions = self._extract_interrupt_questions(state)
                logger.info(
                    "Graph interrupted [chat=%s]: %d question(s), next=%s",
                    self.chat_id,
                    len(questions),
                    state.next,
                )
                if questions:
                    self.chat.pending_questions = questions
                    yield AskQuestionEvent(questions=questions)

                content = "".join(content_parts).strip()
                thinking = "".join(thinking_parts) if thinking_parts else None
                has_cot = thinking or tool_steps
                elapsed_s = time.perf_counter() - t0
                partial_msg = ChatMessage(
                    role="assistant",
                    content=content,
                    msg_id=msg_id,
                    code=self.turn.code,
                    tool_steps=tool_steps,
                    asked_questions=questions if questions else None,
                    thinking=thinking,
                    thinking_duration_s=round(elapsed_s, 1) if has_cot and elapsed_s else None,
                )
                partial_msg.figs = list(self.turn.figs)
                self.chat.messages.append(partial_msg)

                self.chat.pending_msg_id = msg_id
                yield DoneEvent(
                    loop_result=LoopResult(
                        content=content, pending=True, figs=list(self.turn.figs)
                    ),
                    msg_id=msg_id,
                )
            else:
                elapsed_s = time.perf_counter() - t0
                self._finalize_chat(
                    content_parts,
                    tool_steps,
                    thinking_parts,
                    msg_id,
                    selected_card_ids,
                    elapsed_s=elapsed_s,
                )
                last_msg = self.chat.messages[-1]
                if last_msg.proposals:
                    yield CardProposalsEvent(proposals=last_msg.proposals)
                yield DoneEvent(
                    loop_result=make_loop_result(content_parts, self.turn),
                    msg_id=msg_id,
                )

                if auto_name_query and len(self.chat.messages) == 2:
                    title = await self._generate_title(auto_name_query)
                    if title:
                        self._pending_title = title
                        yield ChatRenamedEvent(chat_id=self.chat_id, title=title)
        except Exception as exc:
            logger.error(
                "chat failed [project=%s, chat=%s]",
                self._project.project_id,
                self.chat_id,
                exc_info=True,
            )
            detail = str(exc).strip() or type(exc).__name__
            yield DoneEvent(
                loop_result=LoopResult(content=f"Something went wrong: {detail}", error=detail),
                msg_id=msg_id,
            )

        logger.info(
            "Chat done [project=%s, chat=%s] (%.1fs)",
            self._project.project_id,
            self.chat_id,
            time.perf_counter() - t0,
        )

    @staticmethod
    def _truncate_title(text: str, max_words: int = 6) -> str:
        words = text.split()
        title = " ".join(words[:max_words])
        if len(words) > max_words:
            title += "..."
        return title

    async def _generate_title(self, user_message: str) -> str | None:
        fallback = self._truncate_title(user_message)
        try:
            llm = make_llm(
                self._project.model,
                self._project.api_key,
                temperature=0.3,
                include_thoughts=False,
            )
            resp = await llm.ainvoke(
                f"Generate a concise title (max 6 words) for a conversation that starts with "
                f"this user message. Return ONLY the title, no quotes or punctuation at the "
                f"end.\n\nUser message: {user_message}"
            )
            raw = resp.content
            if isinstance(raw, list):
                raw = "".join(
                    part if isinstance(part, str) else part.get("text", "") for part in raw
                )
            title = raw.strip().strip('"').strip("'")
            if title:
                logger.info("Auto-generated title for chat=%s: %s", self.chat_id, title)
                return title
        except Exception:
            logger.warning(
                "Failed to generate chat title [chat=%s], using fallback",
                self.chat_id,
                exc_info=True,
            )
        return fallback

    def _build_user_message(self, query: str, card_ctx: str | None) -> str:
        parts = []
        if card_ctx:
            parts.append(card_ctx)
        if self._project.sources.is_empty:
            parts.append(f'User query: "{query}"')
        else:
            parts.append(
                DATA_QUERY.format(
                    source_context=self._project.sources.combined_context(),
                    query=query,
                )
            )
        return "\n\n".join(parts)

    def _make_todo_event(self) -> TodoUpdateEvent:
        return TodoUpdateEvent(todos=list(self.chat.todos))

    def _accumulate(self, event, content_parts, tool_steps, thinking_parts):
        if isinstance(event, TextChunkEvent):
            content_parts.append(event.chunk)
        elif isinstance(event, ThinkingEvent):
            thinking_parts.append(event.content)
        elif isinstance(event, ToolCallEvent):
            tool_steps.append(
                ToolStep(
                    tool_name=event.tool_name,
                    arguments_summary=event.arguments_summary,
                    success=True,
                    summary="",
                    duration_ms=0,
                )
            )
        elif isinstance(event, ToolResultEvent) and tool_steps:
            tool_steps[-1].success = event.success
            tool_steps[-1].summary = event.summary
            tool_steps[-1].duration_ms = event.duration_ms

    def _extract_interrupt_questions(self, state) -> list[Question]:
        if not state.tasks:
            return []
        task = state.tasks[0]
        if not task.interrupts:
            return []
        raw_questions = task.interrupts[0].value.get("questions", [])
        return [
            Question(
                question=q.get("question", ""),
                header=q.get("header", ""),
                options=[
                    Choice(label=o.get("label", ""), description=o.get("description", ""))
                    for o in q.get("options", [])
                ],
                multi_select=q.get("multi_select", False),
            )
            for q in raw_questions
        ]

    def _finalize_chat(
        self,
        content_parts,
        tool_steps,
        thinking_parts,
        msg_id,
        selected_card_ids=None,
        elapsed_s: float | None = None,
    ):
        content = "".join(content_parts).strip()
        figs = list(self.turn.figs)
        code = self.turn.code

        proposals = []
        selected_cards = [
            c for c in (self._project.dashboard_cards or []) if c.id in (selected_card_ids or [])
        ]
        for card in selected_cards:
            proposed_fig = self.turn.card_updates.get(card.id)
            if proposed_fig is not None:
                proposals.append(
                    CardProposal(
                        proposal_id=uuid.uuid4().hex[:8],
                        card_id=card.id,
                        card_title=card.title,
                        current_fig=card.fig,
                        current_code=card.code,
                        current_value=card.value,
                        proposed_fig=proposed_fig,
                        proposed_code=code,
                        proposed_value=None,
                    )
                )

        thinking = "".join(thinking_parts) if thinking_parts else None
        has_cot = thinking or tool_steps
        msg = ChatMessage(
            role="assistant",
            content=content,
            msg_id=msg_id,
            code=code,
            tool_steps=tool_steps,
            todos=[TodoItem(id=t.id, content=t.content, status=t.status) for t in self.chat.todos]
            if self.chat.todos
            else [],
            thinking=thinking,
            thinking_duration_s=round(elapsed_s, 1) if has_cot and elapsed_s else None,
        )
        msg.figs = figs
        msg.proposals = proposals
        self.chat.messages.append(msg)
