from __future__ import annotations

import logging

from aiogram import Router
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message

from claw.config import Config
from claw.core.engine import ClaudeEngine
from claw.core.history import Turn
from claw.core.intent import Intent, classify
from claw.core.session import SessionManager, SessionError
from claw.rag.pipeline import RAGPipeline
from claw.telegram.handlers import code as code_handler
from claw.telegram.handlers import monitor as monitor_handler
from claw.telegram.handlers import remote as remote_handler
from claw.telegram.handlers import terminal as terminal_handler
from claw.telegram.handlers import scrape as scrape_handler
from claw.telegram.handlers import tasks as tasks_handler
from claw.telegram.handlers import translate as translate_handler

logger = logging.getLogger(__name__)

router = Router()

_engine: ClaudeEngine | None = None
_sessions: SessionManager | None = None
_config: Config | None = None
_rag: RAGPipeline | None = None


def setup(
    config: Config,
    engine: ClaudeEngine,
    sessions: SessionManager,
    rag: RAGPipeline | None = None,
) -> None:
    global _engine, _sessions, _config, _rag
    _engine = engine
    _sessions = sessions
    _config = config
    _rag = rag


def _session_key(user_id: int) -> str:
    return f"user-{user_id}"


async def _send_response(message: Message, processing: Message, text: str) -> None:
    if len(text) > 4096:
        chunks = [text[i:i + 4096] for i in range(0, len(text), 4096)]
        await _safe_edit(processing, chunks[0])
        for chunk in chunks[1:]:
            await _safe_send(message, chunk)
    else:
        await _safe_edit(processing, text)


async def _safe_edit(msg: Message, text: str) -> None:
    try:
        await msg.edit_text(text, parse_mode=ParseMode.MARKDOWN)
    except Exception:
        await msg.edit_text(text)


async def _safe_send(msg: Message, text: str) -> None:
    try:
        await msg.answer(text, parse_mode=ParseMode.MARKDOWN)
    except Exception:
        await msg.answer(text)


async def _handle_chat(message: Message, text: str, user_id: int) -> None:
    session_name = _session_key(user_id)
    history = _sessions.load(session_name)
    processing = await message.answer("Thinking...")

    if _rag and _rag.index.total_vectors > 0:
        try:
            await processing.edit_text("Searching your knowledge...")
        except Exception:
            pass
        rag_result = await _rag.query(text)

        if rag_result.gate_passed:
            response = rag_result.answer
            if rag_result.sources:
                response += "\n\nSources:\n" + "\n".join(
                    f"  {s}" for s in rag_result.sources
                )
            response += f"\n\n(Confidence: {rag_result.confidence:.0%} | {rag_result.chunks_used} chunks)"

            _sessions.append(session_name, Turn.user(text), Turn.assistant(response))
            await _send_response(message, processing, response)
            logger.info(
                "user=%d rag=true confidence=%.2f chunks=%d",
                user_id, rag_result.confidence, rag_result.chunks_used,
            )
            return

    result = await _engine.ask(
        message=text,
        history=history,
        max_history_turns=_config.max_history_turns,
    )

    _sessions.append(session_name, Turn.user(text), Turn.assistant(result.response))
    await _send_response(message, processing, result.response)

    token_info = f"~{result.prompt_tokens + result.response_tokens} tokens | {result.model}"
    if result.truncated:
        token_info += " | history truncated"
    logger.info("user=%d tokens=%s", user_id, token_info)


async def _handle_model_switch(message: Message, model: str) -> None:
    old_model = _engine.model
    _engine.model = model
    await message.answer(f"Switched from {old_model} to {model}.")


async def _handle_session_list(message: Message) -> None:
    sessions = _sessions.list_sessions()
    if not sessions:
        await message.answer("No sessions yet.")
        return

    lines = []
    for name in sessions:
        stats = _sessions.stats(name)
        lines.append(f"  {name} ({stats['turns']} turns, ~{stats['estimated_tokens']} tokens)")

    await message.answer("Sessions:\n" + "\n".join(lines))


async def _handle_session_branch(message: Message, user_id: int, target: str) -> None:
    source = _session_key(user_id)
    try:
        _sessions.branch(source, target)
        await message.answer(f"Branched current session to '{target}'.")
    except SessionError as e:
        await message.answer(str(e))


async def _handle_session_clear(message: Message, user_id: int) -> None:
    session_name = _session_key(user_id)
    _sessions.delete(session_name)
    await message.answer("Session cleared. Fresh start.")


async def _handle_session_stats(message: Message, user_id: int) -> None:
    session_name = _session_key(user_id)
    if not _sessions.exists(session_name):
        await message.answer("No session yet. Send a message to start.")
        return

    stats = _sessions.stats(session_name)
    lines = [
        f"Turns: {stats['turns']}",
        f"Your messages: {stats['user_messages']}",
        f"Claw responses: {stats['assistant_messages']}",
        f"Total chars: {stats['total_chars']:,}",
        f"Estimated tokens: ~{stats['estimated_tokens']:,}",
        f"Model: {_engine.model}",
    ]
    if _rag:
        lines.append(f"Knowledge chunks: {_rag.index.total_vectors}")
    await message.answer("\n".join(lines))


async def _handle_help(message: Message) -> None:
    lines = [
        "Just talk to me naturally. Examples:",
        "",
        '  "save this https://..." - scrape a page',
        '  "grab everything from https://..." - deep crawl',
        '  "my sources" - list saved pages',
        '  "how much do I know" - knowledge stats',
        '  "delete https://..." - remove a source',
        '  "add task fix the login bug high priority" - add task',
        '  "my tasks" - list active tasks',
        '  "done abc123" - complete a task',
        '  "remind me to deploy at 2026-03-26 15:00"',
        '  "my reminders" - list reminders',
        '  "briefing" or "good morning" - daily summary',
        '  "switch to opus" - change model',
        '  "start fresh" - clear history',
        "",
        "Ask anything — answers from your knowledge base",
        "when relevant, otherwise general knowledge.",
    ]
    await message.answer("\n".join(lines))


_INTENT_MAP = {
    Intent.HELP: lambda msg, text, uid: _handle_help(msg),
    Intent.SESSION_LIST: lambda msg, text, uid: _handle_session_list(msg),
    Intent.SESSION_CLEAR: lambda msg, text, uid: _handle_session_clear(msg, uid),
    Intent.SESSION_STATS: lambda msg, text, uid: _handle_session_stats(msg, uid),
    Intent.KNOWLEDGE_SOURCES: lambda msg, text, uid: scrape_handler.handle_sources(msg),
    Intent.KNOWLEDGE_STATS: lambda msg, text, uid: scrape_handler.handle_knowledge_stats(msg),
    Intent.TASK_LIST: lambda msg, text, uid: tasks_handler.handle_task_list(msg, uid),
    Intent.REMINDER_LIST: lambda msg, text, uid: tasks_handler.handle_reminder_list(msg, uid),
    Intent.BRIEFING: lambda msg, text, uid: tasks_handler.handle_briefing(msg, uid),
    Intent.WATCH_LIST: lambda msg, text, uid: monitor_handler.handle_watch_list(msg, uid),
}


@router.message(Command("start"))
async def handle_start(message: Message) -> None:
    name = message.from_user.first_name if message.from_user else "there"

    welcome = (
        f"Hey {name}! I'm Claw — your personal AI second brain.\n"
        "\n"
        "I live in your Telegram. You talk to me like a person, "
        "no special commands needed. I remember everything you "
        "feed me and answer from YOUR data.\n"
        "\n"
        "Here's how it works:\n"
        "\n"
        "-- STEP 1: Feed me knowledge --\n"
        "\n"
        "Send me any URL:\n"
        "  Just paste a link, I'll scrape it and save the content.\n"
        "  Example: https://docs.python.org/3/tutorial/\n"
        "\n"
        "Deep crawl an entire site:\n"
        '  "grab everything from https://fastapi.tiangolo.com"\n'
        '  "crawl https://docs.python.org go 3 levels deep"\n'
        "\n"
        "Send me files:\n"
        "  PDF, DOCX, TXT, MD, CSV, JSON, PY, HTML\n"
        "  Just drag and drop. I extract text and index it.\n"
        "\n"
        "Send a voice message:\n"
        "  I transcribe it to text automatically.\n"
    )
    await message.answer(welcome)

    features = (
        "-- STEP 2: Ask me anything --\n"
        "\n"
        "I search YOUR saved data first. If I find a match,\n"
        "I answer from your knowledge with source links.\n"
        "If not, I use Claude's general knowledge and tell you.\n"
        "\n"
        "Examples:\n"
        '  "what does FastAPI say about authentication?"\n'
        '  "summarize what I saved about Python decorators"\n'
        '  "compare the articles I have about RAG"\n'
        "\n"
        "-- STEP 3: Stay productive --\n"
        "\n"
        "Tasks:\n"
        '  "add task fix login bug high priority"\n'
        '  "add task deploy by 2026-04-01"\n'
        '  "my tasks" to see active tasks\n'
        '  "done abc123" to complete a task\n'
        "\n"
        "Reminders:\n"
        '  "remind me to check server at 2026-03-26 15:00"\n'
        '  "my reminders" to see pending ones\n'
        "  I'll ping you at the exact time.\n"
        "\n"
        "Daily briefing:\n"
        '  "good morning" or "briefing"\n'
        "  Shows: due tasks, reminders, knowledge stats\n"
    )
    await message.answer(features)

    tools = (
        "-- EXTRA TOOLS --\n"
        "\n"
        "Website monitoring:\n"
        '  "watch https://competitor.com every 6h"\n'
        "  I check periodically and alert you if content changes.\n"
        '  "my watches" to see tracked sites\n'
        "\n"
        "Translation:\n"
        '  "translate to Uzbek: how are you?"\n'
        '  "translate to Russian: meeting at 3pm"\n'
        "  Works with any language.\n"
        "\n"
        "Run Python code:\n"
        "  Send code in ```python blocks.\n"
        "  I execute it and return the output.\n"
        "\n"
        "Remote server control:\n"
        '  "my servers" to see connected servers\n'
        '  "vps> ls -la" runs command on your VPS\n'
        '  "vps> docker ps" check containers remotely\n'
        '  "vps> claude -p \'your prompt\'" use Claude on VPS\n'
        "\n"
        "Local terminal:\n"
        '  "$ git status" runs on this machine\n'
        '  "$ python --version"\n'
        "\n"
        "-- SETTINGS --\n"
        "\n"
        '  "use opus" or "use haiku" — switch AI model\n'
        '  "stats" — see session token usage\n'
        '  "start fresh" — clear conversation history\n'
        '  "branch this as research" — fork the session\n'
        '  "show sessions" — list all saved sessions\n'
        '  "my sources" — see all saved knowledge\n'
        '  "how much do I know" — knowledge base stats\n'
        '  "delete https://..." — remove a source\n'
        "\n"
        "That's it. No commands to memorize.\n"
        "Just talk to me like a person.\n"
        "\n"
        "Try it now — send me a URL or ask me something."
    )
    await message.answer(tools)


@router.message(Command("menu"))
async def handle_menu(message: Message) -> None:
    lines = [
        "What do you need?\n",
        "KNOWLEDGE",
        "  Send a URL — I scrape and save it",
        "  Send a file (PDF/DOCX/TXT) — I extract and index",
        '  "my sources" — list saved pages',
        '  "how much do I know" — knowledge stats',
        '  "delete https://..." — remove a source',
        "",
        "ASK",
        "  Just type your question",
        "  I search your data first, then Claude",
        "",
        "TASKS",
        '  "add task [description]" — create task',
        '  "my tasks" — list active tasks',
        '  "done [id]" — complete a task',
        "",
        "REMINDERS",
        '  "remind me [text] at [date time]"',
        '  "my reminders" — list pending',
        "",
        "BRIEFING",
        '  "good morning" or "briefing"',
        "",
        "MONITOR",
        '  "watch https://..." — track site changes',
        '  "my watches" — list tracked sites',
        "",
        "TERMINAL",
        '  "$ [command]" — run on local machine',
        '  "vps> [command]" — run on remote server',
        '  "my servers" — list connected servers',
        "",
        "TOOLS",
        '  "translate to [lang]: [text]"',
        "  Send ```python code blocks to execute",
        "",
        "SETTINGS",
        '  "use opus/haiku/sonnet" — switch model',
        '  "stats" — session info',
        '  "start fresh" — clear history',
    ]
    await message.answer("\n".join(lines))


@router.message()
async def handle_message(message: Message) -> None:
    if not message.text or not message.from_user:
        return

    text = message.text.strip()
    if not text:
        return

    user_id = message.from_user.id
    classified = classify(text)

    if classified.intent == Intent.CHAT:
        await _handle_chat(message, text, user_id)
    elif classified.intent == Intent.MODEL_SWITCH:
        await _handle_model_switch(message, classified.params["model"])
    elif classified.intent == Intent.SESSION_BRANCH:
        await _handle_session_branch(message, user_id, classified.params["target"])
    elif classified.intent == Intent.SCRAPE:
        await scrape_handler.handle_scrape(message, classified.params["url"])
    elif classified.intent == Intent.CRAWL:
        await scrape_handler.handle_crawl(message, classified.params["url"], classified.params["depth"])
    elif classified.intent == Intent.KNOWLEDGE_DELETE:
        await scrape_handler.handle_delete(message, classified.params["url"])
    elif classified.intent == Intent.TASK_ADD:
        await tasks_handler.handle_task_add(message, user_id, classified.params["title"], classified.params["priority"], classified.params["deadline"])
    elif classified.intent == Intent.TASK_DONE:
        await tasks_handler.handle_task_done(message, classified.params["task_id"])
    elif classified.intent == Intent.REMINDER_ADD:
        await tasks_handler.handle_reminder_add(message, user_id, classified.params["text"], classified.params["remind_at"])
    elif classified.intent == Intent.WATCH_ADD:
        await monitor_handler.handle_watch_add(message, user_id, classified.params["url"], classified.params["interval_hours"])
    elif classified.intent == Intent.WATCH_REMOVE:
        await monitor_handler.handle_watch_remove(message, classified.params["target"])
    elif classified.intent == Intent.RUN_CODE:
        await code_handler.handle_run_code(message, classified.params["code"], classified.params["language"])
    elif classified.intent == Intent.TRANSLATE:
        await translate_handler.handle_translate(message, classified.params["text"], classified.params["target_lang"])
    elif classified.intent == Intent.SHELL:
        await terminal_handler.handle_shell(message, classified.params["command"], classified.params["session"])
    elif classified.intent == Intent.TERMINAL_CREATE:
        await terminal_handler.handle_session_create(message, classified.params["name"], classified.params["cwd"])
    elif classified.intent == Intent.TERMINAL_LIST:
        await terminal_handler.handle_session_list(message)
    elif classified.intent == Intent.REMOTE:
        await remote_handler.handle_remote(message, classified.params["server"], classified.params["command"])
    elif classified.intent == Intent.SERVER_LIST:
        await remote_handler.handle_server_list(message)
    elif classified.intent in _INTENT_MAP:
        await _INTENT_MAP[classified.intent](message, text, user_id)
