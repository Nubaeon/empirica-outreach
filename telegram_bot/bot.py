"""
Empirica Telegram Bot - Epistemic AI Bot

Architecture (mirrors Discord bot):
- Ollama: Fast responses (praxis - action/doing)
- Claude CLI: Deep investigation (noesis - thinking) - uses MAX OAuth
- Qdrant: Memory retrieval (eidetic facts + episodic narratives)
- Empirica: Session tracking, Sentinel gates, CASCADE workflow

Usage:
1. Get bot token from @BotFather on Telegram
2. Set TELEGRAM_BOT_TOKEN env var
3. Run: python bot.py

No API keys needed for Claude - uses your local MAX subscription OAuth.
"""

import os
import asyncio
import subprocess
import json
import logging
from datetime import datetime
from typing import Optional, Dict, List
from dataclasses import dataclass, field

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# Optional: aiohttp for Ollama
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
PROJECT_ID = os.getenv("EMPIRICA_PROJECT_ID", "ea2f33a4-d808-434b-b776-b7246bd6134a")
USE_OLLAMA = os.getenv("USE_OLLAMA", "1").lower() in ("1", "true", "yes")

# Maximum conversation history
MAX_CONVERSATION_HISTORY = 25


@dataclass
class ConversationSession:
    """Tracks Empirica session per Telegram chat."""
    session_id: str
    chat_id: int
    user_id: int
    created_at: datetime = field(default_factory=datetime.now)
    message_count: int = 0
    moon_phase: str = "🌓"
    conversation_history: List[Dict[str, str]] = field(default_factory=list)

    def add_message(self, role: str, content: str):
        """Add message to conversation history."""
        self.conversation_history.append({"role": role, "content": content})
        if len(self.conversation_history) > MAX_CONVERSATION_HISTORY:
            self.conversation_history = self.conversation_history[-MAX_CONVERSATION_HISTORY:]


# Active sessions: chat_id -> ConversationSession
sessions: Dict[int, ConversationSession] = {}


# ============== EMPIRICA CLI INTEGRATION ==============

async def run_empirica(args: list) -> Optional[Dict]:
    """Run Empirica CLI command."""
    try:
        result = await asyncio.create_subprocess_exec(
            "empirica", *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await result.communicate()
        if result.returncode == 0 and stdout:
            return json.loads(stdout.decode())
        return None
    except Exception as e:
        logger.warning(f"Empirica CLI error: {e}")
        return None


async def create_empirica_session() -> Optional[str]:
    """Create a new Empirica session."""
    result = await run_empirica([
        "session-create",
        "--ai-id", "telegram-bot",
        "--output", "json"
    ])
    if result and result.get("ok"):
        return result.get("session_id")
    return None


# ============== MEMORY RETRIEVAL ==============

async def search_memory(query: str, limit: int = 3) -> Dict:
    """Search eidetic and episodic memory."""
    try:
        import sys
        sys.path.insert(0, "/home/yogapad/empirical-ai/empirica")
        from empirica.core.qdrant.vector_store import search_eidetic, search_episodic

        eidetic_results = search_eidetic(
            project_id=PROJECT_ID,
            query=query,
            min_confidence=0.5,
            limit=limit
        )

        episodic_results = search_episodic(
            project_id=PROJECT_ID,
            query=query,
            limit=limit
        )

        return {
            "ok": True,
            "eidetic": [
                {"content": r.get("content", "")[:200], "confidence": r.get("confidence", 0.5)}
                for r in eidetic_results
            ],
            "episodic": [
                {"narrative": r.get("narrative", "")[:150], "outcome": r.get("outcome")}
                for r in episodic_results
            ],
            "has_context": bool(eidetic_results or episodic_results)
        }
    except Exception as e:
        logger.warning(f"Memory search error: {e}")
        return {"ok": False, "eidetic": [], "episodic": [], "has_context": False}


def format_memory_context(memory: Dict) -> str:
    """Format memory results for LLM context."""
    if not memory.get("has_context"):
        return ""

    parts = []
    if memory.get("eidetic"):
        parts.append("**Relevant Facts:**")
        for f in memory["eidetic"][:3]:
            parts.append(f"- [{f['confidence']:.0%}] {f['content'][:80]}...")

    if memory.get("episodic"):
        parts.append("\n**Past Work:**")
        for e in memory["episodic"][:2]:
            parts.append(f"- {e['narrative'][:60]}... ({e.get('outcome', '?')})")

    return "\n".join(parts)


# ============== SCOUT AGENT ==============

def scout_assess(message: str) -> Dict:
    """Fast assessment of message (domain, complexity, action)."""
    message_lower = message.lower()

    # Domain detection
    domains = {
        "empirica": ["empirica", "cascade", "epistemic", "preflight", "postflight"],
        "memory": ["memory", "eidetic", "episodic", "remember", "recall"],
        "ai": ["ai", "llm", "claude", "model", "agent", "vector"],
        "technical": ["code", "api", "error", "bug", "install"],
    }

    detected_domain = "general"
    for domain, keywords in domains.items():
        if any(kw in message_lower for kw in keywords):
            detected_domain = domain
            break

    # Complexity
    complex_triggers = ["explain", "how does", "why", "analyze", "deep dive"]
    is_complex = any(t in message_lower for t in complex_triggers) or len(message) > 200

    return {
        "domain": detected_domain,
        "complexity": "complex" if is_complex else "simple",
        "action": "investigate" if is_complex else "answer",
        "confidence": 0.4 if is_complex else 0.7
    }


# ============== FACTSCORER ==============

def factscorer_validate(response: str, memory_context: str) -> Dict:
    """Validate response confidence."""
    confidence = 0.5

    if memory_context:
        confidence += 0.2

    hedges = ["i think", "might be", "possibly", "not sure"]
    if any(h in response.lower() for h in hedges):
        confidence += 0.1

    overconfident = ["definitely", "absolutely", "always", "never"]
    if any(o in response.lower() for o in overconfident) and not memory_context:
        confidence -= 0.2

    # Moon phase
    if confidence >= 0.85:
        moon = "🌕"
    elif confidence >= 0.70:
        moon = "🌔"
    elif confidence >= 0.50:
        moon = "🌓"
    elif confidence >= 0.30:
        moon = "🌒"
    else:
        moon = "🌑"

    return {"confidence": confidence, "moon": moon, "grounded": bool(memory_context)}


# ============== LLM BACKENDS ==============

async def call_ollama(messages: List[Dict], system: str = None) -> str:
    """Call Ollama for fast responses (praxis)."""
    if not AIOHTTP_AVAILABLE:
        return "Ollama not available (aiohttp not installed)"

    try:
        prompt = ""
        if system:
            prompt = f"System: {system}\n\n"
        for msg in messages:
            role = "User" if msg["role"] == "user" else "Assistant"
            prompt += f"{role}: {msg['content']}\n\n"
        prompt += "Assistant:"

        async with aiohttp.ClientSession() as http:
            async with http.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"num_predict": 1024}
                },
                timeout=aiohttp.ClientTimeout(total=60)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("response", "").strip()
                return f"Ollama error: {resp.status}"
    except Exception as e:
        logger.error(f"Ollama error: {e}")
        return f"Ollama error: {e}"


async def call_claude_cli(task: str, context: str = "") -> str:
    """Call Claude CLI for deep investigation (noesis)."""
    try:
        prompt = f"""You are an epistemic investigation agent. Analyze this deeply:

TASK: {task}

{f"CONTEXT FROM MEMORY:{chr(10)}{context}" if context else ""}

Instructions:
1. Break down what knowledge is needed
2. Identify what you DO know vs DON'T know
3. Be epistemically honest - say "I don't know" when uncertain
4. Keep response under 1000 chars for Telegram"""

        result = await asyncio.create_subprocess_exec(
            "claude", "-p", prompt,
            "--output-format", "text",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await result.communicate()

        if result.returncode == 0:
            return stdout.decode().strip()[:1500]  # Telegram limit
        return f"Investigation error: {stderr.decode()[:200]}"

    except FileNotFoundError:
        return "Claude CLI not found. Install claude-code."
    except Exception as e:
        return f"Investigation error: {e}"


# ============== MESSAGE PROCESSING ==============

async def process_message(session: ConversationSession, message: str) -> str:
    """Process message through epistemic pipeline."""
    session.message_count += 1
    session.add_message("user", message)

    # 1. Scout assessment
    scout = scout_assess(message)

    # 2. Memory retrieval
    memory = await search_memory(message)
    memory_context = format_memory_context(memory)

    # 3. Generate response
    if scout["action"] == "investigate":
        # Deep investigation via Claude CLI
        response = await call_claude_cli(message, memory_context)
        prefix = "🔍 **Investigation:**\n\n"
    else:
        # Fast response via Ollama
        system = f"""You are Empirica Bot, an AI assistant focused on epistemic self-awareness.
Be helpful, concise, and honest about uncertainty. Say "I don't know" when unsure.
Keep responses under 800 chars for Telegram.

{memory_context if memory_context else "No relevant memories found."}"""

        response = await call_ollama(session.conversation_history, system)
        prefix = ""

    # 4. FactScorer validation
    validation = factscorer_validate(response, memory_context)
    session.moon_phase = validation["moon"]

    # Format final response
    grounding = " 📚" if validation["grounded"] else ""
    full_response = f"{validation['moon']}{grounding} {prefix}{response}"

    session.add_message("assistant", full_response)

    # Log to Empirica
    if session.session_id and memory.get("has_context"):
        await run_empirica([
            "finding-log",
            "--session-id", session.session_id,
            "--finding", f"Telegram query matched {len(memory.get('eidetic', []))} facts",
            "--impact", "0.3"
        ])

    return full_response


# ============== TELEGRAM HANDLERS ==============

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    # Create Empirica session
    session_id = await create_empirica_session()

    session = ConversationSession(
        session_id=session_id or f"tg-{chat_id}",
        chat_id=chat_id,
        user_id=user_id
    )
    sessions[chat_id] = session

    await update.message.reply_text(
        "🧠 **Empirica Bot**\n\n"
        "I'm an epistemic AI assistant with memory!\n\n"
        "**Pipeline:**\n"
        "• Scout: Assess your question\n"
        "• Search: Retrieve relevant memories (📚)\n"
        "• Generate: Ollama (fast) or Claude (deep)\n"
        "• FactScorer: Confidence validation (moon phase)\n\n"
        "Ask me anything about Empirica, AI, or just chat!",
        parse_mode="Markdown"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    await update.message.reply_text(
        "🧠 **Empirica Bot Commands**\n\n"
        "/start - Start new session\n"
        "/help - Show this message\n"
        "/status - Show epistemic status\n"
        "/clear - Clear conversation history\n\n"
        "**Moon Phases:**\n"
        "🌕 High confidence\n"
        "🌔 Good confidence\n"
        "🌓 Moderate confidence\n"
        "🌒 Low confidence\n"
        "🌑 Very uncertain\n\n"
        "📚 = Response grounded in memory",
        parse_mode="Markdown"
    )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /status command."""
    chat_id = update.effective_chat.id
    session = sessions.get(chat_id)

    if not session:
        await update.message.reply_text("No active session. Send /start first.")
        return

    await update.message.reply_text(
        f"**Epistemic Status**\n\n"
        f"Session: `{session.session_id[:8]}...`\n"
        f"Messages: {session.message_count}\n"
        f"Moon Phase: {session.moon_phase}\n"
        f"History: {len(session.conversation_history)} msgs",
        parse_mode="Markdown"
    )


async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /clear command."""
    chat_id = update.effective_chat.id
    if chat_id in sessions:
        sessions[chat_id].conversation_history = []
        sessions[chat_id].message_count = 0
        await update.message.reply_text("🧹 Conversation cleared!")
    else:
        await update.message.reply_text("No active session.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle regular messages."""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    message = update.message.text

    # Get or create session
    if chat_id not in sessions:
        session_id = await create_empirica_session()
        sessions[chat_id] = ConversationSession(
            session_id=session_id or f"tg-{chat_id}",
            chat_id=chat_id,
            user_id=user_id
        )

    session = sessions[chat_id]

    # Show typing indicator
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    # Process message
    response = await process_message(session, message)

    # Send response (split if too long)
    if len(response) > 4000:
        for i in range(0, len(response), 4000):
            await update.message.reply_text(response[i:i+4000], parse_mode="Markdown")
    else:
        await update.message.reply_text(response, parse_mode="Markdown")


def main() -> None:
    """Start the bot."""
    if not TELEGRAM_BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN not set")
        print("Get a token from @BotFather on Telegram")
        return

    print("═══════════════════════════════════════════")
    print("   Empirica Telegram Bot")
    print("═══════════════════════════════════════════")
    print()

    # Check backends
    if USE_OLLAMA and AIOHTTP_AVAILABLE:
        print(f"✓ Ollama: {OLLAMA_URL} model={OLLAMA_MODEL}")
    else:
        print("⚠ Ollama not configured (will use Claude CLI only)")

    print("✓ Claude CLI: Deep investigation (noesis)")
    print()

    # Build application
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start polling
    print("Bot started! Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
