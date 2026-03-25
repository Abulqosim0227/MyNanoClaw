from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any


class Intent(Enum):
    CHAT = auto()
    MODEL_SWITCH = auto()
    SESSION_LIST = auto()
    SESSION_BRANCH = auto()
    SESSION_CLEAR = auto()
    SESSION_STATS = auto()
    HELP = auto()
    SCRAPE = auto()
    CRAWL = auto()
    KNOWLEDGE_SOURCES = auto()
    KNOWLEDGE_STATS = auto()
    KNOWLEDGE_DELETE = auto()
    TASK_ADD = auto()
    TASK_LIST = auto()
    TASK_DONE = auto()
    REMINDER_ADD = auto()
    REMINDER_LIST = auto()
    BRIEFING = auto()
    WATCH_ADD = auto()
    WATCH_LIST = auto()
    WATCH_REMOVE = auto()
    RUN_CODE = auto()
    TRANSLATE = auto()
    SHELL = auto()
    TERMINAL_CREATE = auto()
    TERMINAL_LIST = auto()
    REMOTE = auto()
    SERVER_LIST = auto()


@dataclass(frozen=True)
class ClassifiedIntent:
    intent: Intent
    params: dict[str, Any]
    confidence: float

    @staticmethod
    def chat() -> ClassifiedIntent:
        return ClassifiedIntent(intent=Intent.CHAT, params={}, confidence=1.0)


_URL_PATTERN = re.compile(r"(https?://[^\s]+)")

_MODEL_PATTERN = re.compile(
    r"(?:switch\s+to|use|change\s+(?:to|model\s+to)?|set\s+model\s+(?:to)?)\s+"
    r"(sonnet|opus|haiku)",
    re.IGNORECASE,
)

_SCRAPE_PATTERNS = [
    re.compile(r"\b(?:save|scrape|grab|fetch|get|read|index)\s+(?:this\s+)?(?:url|page|site|link)?\s*", re.IGNORECASE),
]

_CRAWL_PATTERNS = [
    re.compile(r"\b(?:crawl|grab\s+everything|scrape\s+(?:everything|all|entire|whole))\b", re.IGNORECASE),
    re.compile(r"\bgo\s+(\d+)\s+(?:levels?|pages?|deep)\b", re.IGNORECASE),
    re.compile(r"\b(?:deep|full)\s+(?:scrape|crawl|scan)\b", re.IGNORECASE),
]

_DEPTH_PATTERN = re.compile(r"(?:depth|levels?|deep)\s*(?:=|:)?\s*(\d+)", re.IGNORECASE)
_DEPTH_PATTERN_ALT = re.compile(r"(\d+)\s+(?:levels?|pages?\s+deep)", re.IGNORECASE)

_SESSION_LIST_PATTERNS = [
    re.compile(r"\b(?:show|list|my)\s+sessions?\b", re.IGNORECASE),
    re.compile(r"\bsessions?\s+(?:list|show)\b", re.IGNORECASE),
    re.compile(r"\bwhat\s+sessions?\b", re.IGNORECASE),
]

_SESSION_BRANCH_PATTERN = re.compile(
    r"(?:branch|fork|copy|save)\s+(?:this\s+)?(?:as|to|into|session)?\s*([a-zA-Z0-9_-]+)",
    re.IGNORECASE,
)

_SESSION_CLEAR_PATTERNS = [
    re.compile(r"\b(?:clear|reset|wipe|erase)\s+(?:history|session|chat|conversation)\b", re.IGNORECASE),
    re.compile(r"\bstart\s+(?:over|fresh|new)\b", re.IGNORECASE),
    re.compile(r"\bnew\s+(?:session|chat|conversation)\b", re.IGNORECASE),
]

_SESSION_STATS_PATTERNS = [
    re.compile(r"\b(?:stats?|statistics|metrics|usage)\b", re.IGNORECASE),
    re.compile(r"\bhow\s+(?:many|much)\s+(?:messages?|tokens?|turns?)\b", re.IGNORECASE),
]

_HELP_PATTERNS = [
    re.compile(r"^(?:help|what\s+can\s+you\s+do|commands?)$", re.IGNORECASE),
    re.compile(r"\bwhat\s+(?:are\s+you|do\s+you\s+do)\b", re.IGNORECASE),
]

_KNOWLEDGE_SOURCES_PATTERNS = [
    re.compile(r"\b(?:what|show|list)\s+(?:sites?|sources?|pages?)\s+(?:have\s+I|do\s+I\s+have|saved|scraped)\b", re.IGNORECASE),
    re.compile(r"\b(?:my|show|list)\s+(?:sources?|knowledge|saved\s+pages?)\b", re.IGNORECASE),
    re.compile(r"\bwhat\s+(?:do\s+I\s+)?know\b", re.IGNORECASE),
]

_KNOWLEDGE_STATS_PATTERNS = [
    re.compile(r"\bhow\s+much\s+(?:do\s+I\s+)?know\b", re.IGNORECASE),
    re.compile(r"\bknowledge\s+(?:stats?|size|count)\b", re.IGNORECASE),
    re.compile(r"\bbrain\s+(?:stats?|size)\b", re.IGNORECASE),
]

_KNOWLEDGE_DELETE_PATTERN = re.compile(
    r"\b(?:delete|remove|forget|drop)\s+(?:everything\s+from\s+)?", re.IGNORECASE,
)

_TASK_ADD_PATTERNS = [
    re.compile(r"\b(?:add|create|new)\s+task\b", re.IGNORECASE),
    re.compile(r"\btask\s*:\s*", re.IGNORECASE),
    re.compile(r"\btodo\s*:\s*", re.IGNORECASE),
]

_TASK_ADD_EXTRACT = re.compile(
    r"(?:add\s+task|create\s+task|new\s+task|task\s*:|todo\s*:)\s*(.+)",
    re.IGNORECASE,
)

_TASK_LIST_PATTERNS = [
    re.compile(r"\b(?:show|list|my|what)\s+tasks?\b", re.IGNORECASE),
    re.compile(r"\bwhat\s+(?:do\s+I\s+)?(?:need\s+to\s+do|have\s+to\s+do)\b", re.IGNORECASE),
    re.compile(r"\bpending\s+tasks?\b", re.IGNORECASE),
]

_TASK_DONE_PATTERN = re.compile(
    r"(?:done|complete|finish|check\s+off)\s+(?:task\s+)?([a-f0-9]{6,8})",
    re.IGNORECASE,
)

_REMINDER_ADD_PATTERNS = [
    re.compile(r"\bremind\s+me\b", re.IGNORECASE),
    re.compile(r"\bset\s+(?:a\s+)?reminder\b", re.IGNORECASE),
]

_REMINDER_LIST_PATTERNS = [
    re.compile(r"\b(?:show|list|my)\s+reminders?\b", re.IGNORECASE),
    re.compile(r"\bwhat\s+reminders?\b", re.IGNORECASE),
]

_BRIEFING_PATTERNS = [
    re.compile(r"\b(?:daily\s+)?briefing\b", re.IGNORECASE),
    re.compile(r"\bwhat.s\s+(?:new|up)\s+today\b", re.IGNORECASE),
    re.compile(r"\bgood\s+morning\b", re.IGNORECASE),
    re.compile(r"\bmorning\s+(?:briefing|report|update)\b", re.IGNORECASE),
    re.compile(r"\bwhat\s+do\s+I\s+have\s+today\b", re.IGNORECASE),
]

_PRIORITY_PATTERN = re.compile(r"\b(urgent|high|low)\s+priority\b", re.IGNORECASE)
_DEADLINE_PATTERN = re.compile(r"\b(?:by|due|deadline)\s+(\d{4}-\d{2}-\d{2}(?:\s+\d{2}:\d{2})?)\b", re.IGNORECASE)
_REMINDER_TIME_PATTERN = re.compile(r"\b(?:at|on)\s+(\d{4}-\d{2}-\d{2}(?:\s+\d{2}:\d{2})?)\b", re.IGNORECASE)

_WATCH_ADD_PATTERNS = [
    re.compile(r"\b(?:watch|monitor|track)\s+", re.IGNORECASE),
    re.compile(r"\btell\s+me\s+when\s+.+\s+changes?\b", re.IGNORECASE),
    re.compile(r"\balert\s+me\s+(?:if|when)\b", re.IGNORECASE),
]

_WATCH_INTERVAL_PATTERN = re.compile(r"\bevery\s+(\d+)\s*h", re.IGNORECASE)

_WATCH_LIST_PATTERNS = [
    re.compile(r"\b(?:show|list|my)\s+(?:watches|monitors|tracked)\b", re.IGNORECASE),
    re.compile(r"\bwhat\s+(?:am\s+I|are\s+you)\s+(?:watching|monitoring|tracking)\b", re.IGNORECASE),
]

_WATCH_REMOVE_PATTERN = re.compile(
    r"\b(?:stop\s+watching|unwatch|stop\s+monitoring|remove\s+watch)\s+(?:(?:id\s+)?([a-f0-9]{6,8})|(https?://\S+))",
    re.IGNORECASE,
)


_RUN_CODE_PATTERN = re.compile(
    r"(?:run|execute)\s*(?:this)?\s*(?:code|python|script)?\s*[:\n]?\s*```(?:python)?\s*\n?(.*?)```",
    re.IGNORECASE | re.DOTALL,
)

_RUN_CODE_SIMPLE = re.compile(r"\b(?:run|execute)\s+(?:this\s+)?(?:code|python|script)\b", re.IGNORECASE)

_TRANSLATE_PATTERN = re.compile(
    r"\btranslate\s+(?:this\s+)?(?:to\s+)?(\w+)\s*[:\n]?\s*(.+)",
    re.IGNORECASE | re.DOTALL,
)

_TRANSLATE_SIMPLE = re.compile(
    r"\btranslate\s+(?:to\s+)?(\w+)",
    re.IGNORECASE,
)

_SHELL_PATTERN = re.compile(r"^\$\s+(.+)", re.DOTALL)
_SHELL_SESSION_PATTERN = re.compile(r"^(\w+)\$\s+(.+)", re.DOTALL)

_TERMINAL_CREATE_PATTERN = re.compile(
    r"\bterminal\s+(?:new|create|add)\s+(\w+)\s+(.+)", re.IGNORECASE,
)

_TERMINAL_LIST_PATTERNS = [
    re.compile(r"\b(?:show|list|my)\s+terminals?\b", re.IGNORECASE),
    re.compile(r"\bterminal\s+(?:list|sessions?)\b", re.IGNORECASE),
]

_REMOTE_PATTERN = re.compile(r"^(\w+)>\s*(.+)", re.DOTALL)

_SERVER_LIST_PATTERNS = [
    re.compile(r"\b(?:show|list|my)\s+servers?\b", re.IGNORECASE),
    re.compile(r"\bremote\s+servers?\b", re.IGNORECASE),
]


def _extract_url(text: str) -> str:
    match = _URL_PATTERN.search(text)
    return match.group(1).rstrip(".,;:!?)") if match else ""


def _extract_depth(text: str) -> int:
    match = _DEPTH_PATTERN.search(text)
    if match:
        return min(int(match.group(1)), 5)
    match = _DEPTH_PATTERN_ALT.search(text)
    if match:
        return min(int(match.group(1)), 5)
    return 2


def classify(text: str) -> ClassifiedIntent:
    text = text.strip()
    if not text:
        return ClassifiedIntent.chat()

    model_match = _MODEL_PATTERN.search(text)
    if model_match:
        return ClassifiedIntent(
            intent=Intent.MODEL_SWITCH,
            params={"model": model_match.group(1).lower()},
            confidence=0.95,
        )

    remote_match = _REMOTE_PATTERN.match(text)
    if remote_match:
        return ClassifiedIntent(
            intent=Intent.REMOTE,
            params={"server": remote_match.group(1), "command": remote_match.group(2).strip()},
            confidence=0.95,
        )

    for pattern in _SERVER_LIST_PATTERNS:
        if pattern.search(text):
            return ClassifiedIntent(intent=Intent.SERVER_LIST, params={}, confidence=0.9)

    shell_session_match = _SHELL_SESSION_PATTERN.match(text)
    if shell_session_match:
        return ClassifiedIntent(
            intent=Intent.SHELL,
            params={"command": shell_session_match.group(2).strip(), "session": shell_session_match.group(1)},
            confidence=0.95,
        )

    shell_match = _SHELL_PATTERN.match(text)
    if shell_match:
        return ClassifiedIntent(
            intent=Intent.SHELL,
            params={"command": shell_match.group(1).strip(), "session": ""},
            confidence=0.95,
        )

    terminal_create_match = _TERMINAL_CREATE_PATTERN.search(text)
    if terminal_create_match:
        return ClassifiedIntent(
            intent=Intent.TERMINAL_CREATE,
            params={"name": terminal_create_match.group(1), "cwd": terminal_create_match.group(2).strip()},
            confidence=0.95,
        )

    for pattern in _TERMINAL_LIST_PATTERNS:
        if pattern.search(text):
            return ClassifiedIntent(intent=Intent.TERMINAL_LIST, params={}, confidence=0.9)

    for pattern in _HELP_PATTERNS:
        if pattern.search(text):
            return ClassifiedIntent(intent=Intent.HELP, params={}, confidence=0.9)

    code_match = _RUN_CODE_PATTERN.search(text)
    if code_match:
        return ClassifiedIntent(
            intent=Intent.RUN_CODE,
            params={"code": code_match.group(1).strip(), "language": "python"},
            confidence=0.95,
        )

    translate_match = _TRANSLATE_PATTERN.search(text)
    if translate_match:
        return ClassifiedIntent(
            intent=Intent.TRANSLATE,
            params={"target_lang": translate_match.group(1), "text": translate_match.group(2).strip()},
            confidence=0.9,
        )

    url = _extract_url(text)

    remove_match = _WATCH_REMOVE_PATTERN.search(text)
    if remove_match:
        target = remove_match.group(1) or remove_match.group(2) or ""
        return ClassifiedIntent(
            intent=Intent.WATCH_REMOVE,
            params={"target": target.strip()},
            confidence=0.9,
        )

    if url:
        for pattern in _WATCH_ADD_PATTERNS:
            if pattern.search(text):
                interval_match = _WATCH_INTERVAL_PATTERN.search(text)
                hours = int(interval_match.group(1)) if interval_match else 24
                return ClassifiedIntent(
                    intent=Intent.WATCH_ADD,
                    params={"url": url, "interval_hours": min(hours, 168)},
                    confidence=0.95,
                )

        for pattern in _CRAWL_PATTERNS:
            if pattern.search(text):
                return ClassifiedIntent(
                    intent=Intent.CRAWL,
                    params={"url": url, "depth": _extract_depth(text)},
                    confidence=0.95,
                )

        for pattern in _SCRAPE_PATTERNS:
            if pattern.search(text):
                return ClassifiedIntent(
                    intent=Intent.SCRAPE,
                    params={"url": url},
                    confidence=0.9,
                )

        delete_match = _KNOWLEDGE_DELETE_PATTERN.search(text)
        if delete_match:
            return ClassifiedIntent(
                intent=Intent.KNOWLEDGE_DELETE,
                params={"url": url},
                confidence=0.9,
            )

        return ClassifiedIntent(
            intent=Intent.SCRAPE,
            params={"url": url},
            confidence=0.7,
        )

    for pattern in _WATCH_LIST_PATTERNS:
        if pattern.search(text):
            return ClassifiedIntent(intent=Intent.WATCH_LIST, params={}, confidence=0.9)

    for pattern in _BRIEFING_PATTERNS:
        if pattern.search(text):
            return ClassifiedIntent(intent=Intent.BRIEFING, params={}, confidence=0.9)

    done_match = _TASK_DONE_PATTERN.search(text)
    if done_match:
        return ClassifiedIntent(
            intent=Intent.TASK_DONE,
            params={"task_id": done_match.group(1)},
            confidence=0.95,
        )

    for pattern in _TASK_LIST_PATTERNS:
        if pattern.search(text):
            return ClassifiedIntent(intent=Intent.TASK_LIST, params={}, confidence=0.9)

    add_match = _TASK_ADD_EXTRACT.search(text)
    if add_match or any(p.search(text) for p in _TASK_ADD_PATTERNS):
        title = add_match.group(1).strip() if add_match else ""
        priority = "medium"
        p_match = _PRIORITY_PATTERN.search(text)
        if p_match:
            priority = p_match.group(1).lower()
            title = _PRIORITY_PATTERN.sub("", title).strip()
        deadline = ""
        d_match = _DEADLINE_PATTERN.search(text)
        if d_match:
            deadline = d_match.group(1)
            title = _DEADLINE_PATTERN.sub("", title).strip()
        return ClassifiedIntent(
            intent=Intent.TASK_ADD,
            params={"title": title, "priority": priority, "deadline": deadline},
            confidence=0.9,
        )

    for pattern in _REMINDER_ADD_PATTERNS:
        if pattern.search(text):
            time_match = _REMINDER_TIME_PATTERN.search(text)
            remind_at = time_match.group(1) if time_match else ""
            reminder_text = text
            for p in _REMINDER_ADD_PATTERNS:
                reminder_text = p.sub("", reminder_text)
            if time_match:
                reminder_text = _REMINDER_TIME_PATTERN.sub("", reminder_text)
            return ClassifiedIntent(
                intent=Intent.REMINDER_ADD,
                params={"text": reminder_text.strip(), "remind_at": remind_at},
                confidence=0.9,
            )

    for pattern in _REMINDER_LIST_PATTERNS:
        if pattern.search(text):
            return ClassifiedIntent(intent=Intent.REMINDER_LIST, params={}, confidence=0.9)

    for pattern in _KNOWLEDGE_SOURCES_PATTERNS:
        if pattern.search(text):
            return ClassifiedIntent(intent=Intent.KNOWLEDGE_SOURCES, params={}, confidence=0.9)

    for pattern in _KNOWLEDGE_STATS_PATTERNS:
        if pattern.search(text):
            return ClassifiedIntent(intent=Intent.KNOWLEDGE_STATS, params={}, confidence=0.9)

    for pattern in _SESSION_LIST_PATTERNS:
        if pattern.search(text):
            return ClassifiedIntent(intent=Intent.SESSION_LIST, params={}, confidence=0.9)

    branch_match = _SESSION_BRANCH_PATTERN.search(text)
    if branch_match:
        return ClassifiedIntent(
            intent=Intent.SESSION_BRANCH,
            params={"target": branch_match.group(1).lower()},
            confidence=0.9,
        )

    for pattern in _SESSION_CLEAR_PATTERNS:
        if pattern.search(text):
            return ClassifiedIntent(intent=Intent.SESSION_CLEAR, params={}, confidence=0.9)

    for pattern in _SESSION_STATS_PATTERNS:
        if pattern.search(text):
            return ClassifiedIntent(intent=Intent.SESSION_STATS, params={}, confidence=0.85)

    return ClassifiedIntent.chat()
