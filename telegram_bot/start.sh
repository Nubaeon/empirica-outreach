#!/bin/bash
#
# Empirica Telegram Bot - Start Script
#
# Prerequisites:
#   - Ollama running (ollama serve)
#   - TELEGRAM_BOT_TOKEN set (from @BotFather)
#   - Claude CLI authenticated (for deep investigation)

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo -e "${BLUE}   Empirica Telegram Bot                   ${NC}"
echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo ""

# Check token
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    if [ -f .env ]; then
        export $(grep -v '^#' .env | xargs)
    fi
fi

if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo -e "${RED}Error: TELEGRAM_BOT_TOKEN not set${NC}"
    echo ""
    echo "1. Talk to @BotFather on Telegram"
    echo "2. Create a new bot with /newbot"
    echo "3. Copy the token"
    echo "4. Set it: export TELEGRAM_BOT_TOKEN=your_token"
    echo "   Or add to .env file"
    exit 1
fi

# Check Ollama
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Ollama running"
else
    echo "⚠ Ollama not detected. Start with: ollama serve"
fi

# Check Qdrant
if curl -s http://localhost:6333/collections > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Qdrant running (memory enabled)"
else
    echo "⚠ Qdrant not detected. Memory features disabled."
fi

# Check Claude CLI
if command -v claude &> /dev/null; then
    echo -e "${GREEN}✓${NC} Claude CLI available"
else
    echo "⚠ Claude CLI not found"
fi

echo ""
echo "Starting bot..."
echo ""

python bot.py
