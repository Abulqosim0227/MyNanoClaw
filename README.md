# Claw

Your personal AI second brain. Controlled entirely from Telegram.

Claw scrapes the web, stores knowledge, answers from your data, manages tasks, monitors sites, runs code, translates — all through natural conversation. No slash commands. Just talk.

## What It Does

```
You: "save this https://docs.python.org/3/tutorial/"
Claw: Saved: The Python Tutorial
      12,340 words from docs.python.org
      Indexed: 28 chunks for search

You: "what does Python say about decorators?"
Claw: Based on your saved data, decorators are functions that
      modify other functions. The @property decorator...

      Sources:
        docs.python.org/3/tutorial/classes
      Confidence: 94% | 3 chunks

You: "good morning"
Claw: Daily Briefing

      Due today: 2 tasks
        [HIGH] Deploy new version
        [MEDIUM] Review PR #42

      Active tasks: 5
      Upcoming reminders: 1
        2026-03-26 15:00 — Check server status

      Knowledge base: 847 pages, 2.1M words
      Search index: 4,230 chunks
```

## Features

### Knowledge Collector
- **Scrape any URL** — send a link, Claw extracts clean text using [trafilatura](https://github.com/adbar/trafilatura)
- **Deep crawl** — "grab everything from https://..." crawls entire sites (configurable depth)
- **PDF processing** — send a PDF, text is extracted and indexed automatically
- **DOCX/TXT/MD/CSV/JSON/PY/HTML** — all supported, all indexed
- **Voice messages** — transcribed to text using Google Speech Recognition
- **Duplicate detection** — content hashing prevents re-indexing unchanged pages
- **Verification** — re-fetches pages to confirm data was captured correctly

### RAG (Retrieval-Augmented Generation)
- **FAISS vector search** — your documents are chunked, embedded, and indexed locally
- **Local embeddings** — uses `all-MiniLM-L6-v2` (free, no API costs, runs on CPU)
- **Relevance gate** — refuses to answer from data when confidence is below threshold (no hallucination)
- **Source citations** — every answer includes source URLs and confidence score
- **Automatic fallback** — if no match in your data, uses Claude general knowledge (honestly tells you)

### Task Manager
- **Natural language tasks** — "add task fix login bug high priority by 2026-03-30"
- **Priority sorting** — urgent > high > medium > low
- **Deadline tracking** — due dates with daily briefing alerts
- **Complete/cancel** — "done abc123" marks a task complete

### Reminders
- **Set reminders** — "remind me to deploy at 2026-03-26 15:00"
- **Auto-fire** — Claw sends you a Telegram message at the exact time
- **Background loop** — checks every 30 seconds, never misses

### Website Monitoring
- **Watch any URL** — "watch https://competitor.com every 6h"
- **Change detection** — content hashing detects any modification
- **Instant alerts** — Telegram notification the moment a site changes
- **Configurable interval** — check every 1h to 168h (1 week)

### Code Execution
- **Run Python** — send code in \`\`\`python blocks, get output back
- **Error handling** — shows stdout, stderr, and exit code
- **Timeout protection** — 30-second execution limit

### Translation
- **Any language** — "translate to Uzbek: hello world"
- **Powered by Claude** — high quality, context-aware translations

### Session Management
- **Persistent history** — conversations saved as markdown files
- **Branch sessions** — "branch this as research" forks your conversation
- **Token tracking** — see how many tokens each session uses
- **Auto-truncation** — old history compressed to save API costs

### Daily Briefing
- **"good morning"** — get a full summary: tasks, reminders, knowledge stats
- **Due today** — highlights tasks with today's deadline
- **Knowledge growth** — tracks pages, words, and indexed chunks

## Architecture

```
Telegram (aiogram 3)
    |
    v
Intent Classifier (regex, zero API cost)
    |
    +---> Chat (Claude CLI + RAG)
    +---> Scraper (httpx + trafilatura)
    +---> File Processor (PyMuPDF + python-docx + SpeechRecognition)
    +---> Task Manager (JSON persistence)
    +---> Reminder Loop (asyncio, 30s interval)
    +---> Website Monitor (asyncio, configurable interval)
    +---> Code Runner (subprocess, sandboxed)
    +---> Translator (Claude)
    |
    v
Knowledge Layer
    +---> PageStorage (text files + JSON metadata)
    +---> FAISS Index (vector search)
    +---> Embedder (sentence-transformers, CPU)
    +---> RAG Pipeline (retrieve -> gate -> cite -> answer)
```

## Security

- **Chat ID authentication** — only whitelisted Telegram users can interact
- **Rate limiting** — sliding window, configurable requests per minute
- **Input sanitization** — shell injection prevention, null byte stripping, length limits
- **Token masking** — bot token never logged in full
- **Session name validation** — regex-enforced, no path traversal
- **Subprocess timeout** — all external processes have hard time limits
- **File size limits** — PDF 50MB, others 20MB, voice 5 minutes
- **No secrets in code** — everything in `.env`, gitignored

## Quick Start

### Prerequisites

- Python 3.10+
- [Claude CLI](https://docs.anthropic.com/en/docs/claude-code) installed and authenticated
- ffmpeg (for voice messages)

### Installation

```bash
git clone https://github.com/yourusername/claw.git
cd claw
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Configuration

```bash
cp .env.example .env
```

Edit `.env`:

```env
TELEGRAM_BOT_TOKEN=your_token_from_botfather
ALLOWED_CHAT_IDS=your_telegram_user_id
CLAUDE_MODEL=sonnet
MAX_HISTORY_TURNS=20
RATE_LIMIT_PER_MINUTE=15
SESSION_DIR=sessions
```

**Getting your Telegram chat ID:**
1. Message [@userinfobot](https://t.me/userinfobot) on Telegram
2. It replies with your user ID

**Getting a bot token:**
1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot`, follow the prompts
3. Copy the token

### Run

```bash
python main.py
```

Then open Telegram and message your bot.

### Install PyTorch CPU-only (recommended)

The default `pip install` pulls CUDA PyTorch (~5GB). Install CPU-only first:

```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
```

## Usage Examples

### Collecting Knowledge

```
save this https://fastapi.tiangolo.com/tutorial/
grab everything from https://docs.python.org go 3 levels deep
```

Send a PDF, DOCX, or text file directly in Telegram.

### Asking Questions

```
what does FastAPI say about dependency injection?
summarize what I know about Python decorators
how does authentication work based on my saved docs?
```

### Managing Tasks

```
add task deploy v2.0 to production urgent priority by 2026-04-01
my tasks
done a1b2c3d4
```

### Reminders

```
remind me to check server logs at 2026-03-26 18:00
my reminders
```

### Monitoring

```
watch https://competitor.com/pricing every 12h
my watches
stop watching abc12345
```

### Code Execution

````
run this:
```python
import json
data = {"name": "claw", "version": "1.0"}
print(json.dumps(data, indent=2))
```
````

### Translation

```
translate to Russian: The meeting is scheduled for tomorrow at 3pm
translate Uzbek: How does this API work?
```

### Session Control

```
switch to opus
use haiku
stats
start fresh
branch this as research
show sessions
```

### Daily Briefing

```
good morning
briefing
what do I have today
```

## Project Structure

```
claw/
├── claw/
│   ├── config.py              # Settings, env validation
│   ├── core/
│   │   ├── engine.py          # Claude CLI interaction
│   │   ├── history.py         # Markdown conversation persistence
│   │   ├── intent.py          # Natural language intent classifier
│   │   └── session.py         # Session CRUD + branching
│   ├── monitor/
│   │   └── watcher.py         # Website change detection
│   ├── processors/
│   │   ├── document.py        # TXT + DOCX extraction
│   │   ├── pdf.py             # PDF text extraction (PyMuPDF)
│   │   └── voice.py           # Voice transcription (SpeechRecognition)
│   ├── rag/
│   │   ├── chunker.py         # Text splitting with overlap
│   │   ├── embedder.py        # Sentence-transformers embeddings
│   │   ├── gate.py            # Relevance threshold gate
│   │   ├── index.py           # FAISS vector index
│   │   └── pipeline.py        # Full RAG pipeline
│   ├── scraper/
│   │   ├── crawler.py         # Single page + deep crawl
│   │   ├── fetcher.py         # Async HTTP with retry
│   │   ├── parser.py          # HTML extraction (trafilatura)
│   │   ├── storage.py         # Page persistence + metadata
│   │   └── verifier.py        # Post-scrape verification
│   ├── security/
│   │   ├── rate_limiter.py    # Sliding window rate limiter
│   │   └── sanitizer.py       # Input sanitization
│   ├── tasks/
│   │   ├── briefing.py        # Daily briefing generator
│   │   ├── manager.py         # Task CRUD with priorities
│   │   └── reminders.py       # Scheduled reminders
│   └── telegram/
│       ├── bot.py             # Bot factory, wiring
│       ├── middleware.py       # Auth + rate limit middleware
│       └── handlers/
│           ├── chat.py        # Main message router
│           ├── code.py        # Python code execution
│           ├── files.py       # File upload processing
│           ├── monitor.py     # Watch management
│           ├── scrape.py      # URL scraping
│           ├── tasks.py       # Task/reminder management
│           └── translate.py   # Translation
├── tests/                     # 325 tests, 85% coverage
├── main.py                    # Entry point
├── requirements.txt
└── .env.example
```

## Testing

```bash
# Run all tests
python -m pytest tests/ -v

# With coverage
python -m pytest tests/ --cov=claw --cov-report=term-missing

# Specific module
python -m pytest tests/test_intent.py -v
```

## Tech Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| Bot framework | aiogram 3 | Async, modern, well-maintained |
| AI backend | Claude CLI | Best coding model, local execution |
| Web scraping | httpx + trafilatura | Async HTTP + best content extraction |
| Vector search | FAISS (CPU) | Fast, battle-tested, no server needed |
| Embeddings | sentence-transformers | Local, free, no API costs |
| PDF processing | PyMuPDF | Fast, pure Python, no external binaries |
| Voice | SpeechRecognition + pydub | Google API (free tier), ffmpeg for conversion |
| Documents | python-docx | DOCX paragraph extraction |
| ML runtime | PyTorch (CPU-only) | ~200MB vs 5GB CUDA version |

## Token Efficiency

Claw is designed to minimize Claude API token usage:

- **Intent classification** — regex-based, zero API calls
- **History truncation** — only sends last N turns to Claude
- **Auto-compaction** — estimates tokens before sending, trims if needed
- **RAG gate** — low-confidence queries fall back without wasting tokens on bad context
- **Model switching** — use haiku for simple tasks, opus for complex ones

## Roadmap

- [ ] Knowledge graph — automatic topic linking across sources
- [ ] Inline buttons — contextual actions after each response
- [ ] Scheduled scraping — auto-rescrape on schedule
- [ ] Multi-user — support multiple Telegram users with isolated data
- [ ] Web dashboard — browser UI for knowledge management
- [ ] Plugin system — extend with custom handlers

## Contributing

1. Fork the repo
2. Create a feature branch
3. Write tests first (TDD)
4. Ensure 80%+ coverage
5. Submit a PR

## License

MIT
