from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from aiogram import Bot, Dispatcher

from claw.config import Config
from claw.core.engine import ClaudeEngine
from claw.core.session import SessionManager
from claw.rag.embedder import Embedder
from claw.rag.index import VectorIndex
from claw.rag.pipeline import RAGPipeline
from claw.scraper.storage import PageStorage
from claw.security.rate_limiter import RateLimiter
from claw.monitor.watcher import WatchManager, ChangeAlert
from claw.tasks.manager import TaskManager
from claw.tasks.reminders import ReminderManager, Reminder
from claw.telegram.handlers import chat, files, monitor, scrape, tasks, translate
from claw.telegram.middleware import AuthMiddleware, RateLimitMiddleware

logger = logging.getLogger(__name__)

KNOWLEDGE_DIR = Path("knowledge")
INDEX_DIR = Path("knowledge/vectors")
TASKS_DIR = Path("data")


def create_bot(config: Config) -> tuple[Bot, Dispatcher]:
    bot = Bot(token=config.telegram_token)
    dp = Dispatcher()

    dp.message.middleware(AuthMiddleware(config.allowed_chat_ids))
    dp.message.middleware(RateLimitMiddleware(
        RateLimiter(max_requests=config.rate_limit_per_minute)
    ))

    engine = ClaudeEngine(model=config.claude_model)
    sessions = SessionManager(base_dir=config.session_dir)
    storage = PageStorage(base_dir=KNOWLEDGE_DIR)

    embedder = Embedder()
    index = VectorIndex(index_dir=INDEX_DIR)
    rag = RAGPipeline(embedder=embedder, index=index, engine=engine)

    task_mgr = TaskManager(data_dir=TASKS_DIR)

    async def on_reminder_fire(reminder: Reminder) -> None:
        for chat_id in config.allowed_chat_ids:
            try:
                await bot.send_message(chat_id, f"Reminder: {reminder.text}")
            except Exception as e:
                logger.error("Failed to send reminder: %s", e)

    reminder_mgr = ReminderManager(data_dir=TASKS_DIR, on_fire=on_reminder_fire)

    async def on_watch_change(alert: ChangeAlert) -> None:
        for chat_id in config.allowed_chat_ids:
            try:
                await bot.send_message(chat_id, f"Site changed: {alert.watch.url}\n{alert.summary}")
            except Exception as e:
                logger.error("Failed to send watch alert: %s", e)

    watch_mgr = WatchManager(data_dir=TASKS_DIR, on_change=on_watch_change)

    chat.setup(config, engine, sessions, rag=rag)
    scrape.setup(storage, embedder=embedder, index=index)
    files.setup(storage, embedder=embedder, index=index)
    tasks.setup(task_mgr, reminder_mgr, storage, index=index)
    monitor.setup(watch_mgr)
    translate.setup(engine)
    dp.include_router(files.router)
    dp.include_router(chat.router)

    async def _start_background_loops() -> None:
        await asyncio.gather(
            reminder_mgr.start_loop(interval=30),
            watch_mgr.start_loop(interval=300),
        )

    dp.startup.register(lambda: asyncio.create_task(_start_background_loops()))

    logger.info(
        "Bot initialized | model=%s | token=%s | vectors=%d",
        config.claude_model,
        config.masked_token(),
        index.total_vectors,
    )

    return bot, dp
