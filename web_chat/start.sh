#!/bin/bash
#
# Empirica Web Chat - Local Deployment
#
# Prerequisites:
#   - Ollama running (ollama serve)
#   - Qdrant running (or skip memory features)
#   - Claude CLI authenticated (claude auth)
#   - ngrok installed (for public access)
#
# Usage:
#   ./start.sh          # Local only (localhost:8080)
#   ./start.sh --ngrok  # With ngrok tunnel for public access

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo -e "${BLUE}   Empirica Web Chat - Epistemic Pipeline  ${NC}"
echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo ""

# Check Ollama
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Ollama running"
else
    echo "⚠ Ollama not detected. Start with: ollama serve"
    echo "  (Chat will work but responses will be slower via Claude CLI)"
fi

# Check Qdrant
if curl -s http://localhost:6333/collections > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Qdrant running (memory enabled)"
else
    echo "⚠ Qdrant not detected. Memory retrieval will be disabled."
fi

# Check Claude CLI
if command -v claude &> /dev/null; then
    echo -e "${GREEN}✓${NC} Claude CLI available (noesis backend)"
else
    echo "⚠ Claude CLI not found. Deep investigation disabled."
fi

echo ""

# Start with ngrok?
if [[ "$1" == "--ngrok" ]]; then
    echo -e "${BLUE}Starting with ngrok tunnel...${NC}"
    echo ""

    # Start server in background
    python app.py &
    SERVER_PID=$!
    sleep 2

    # Start ngrok
    echo "Starting ngrok..."
    ngrok http 8080 &
    NGROK_PID=$!
    sleep 3

    # Get ngrok URL
    NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "import sys,json; print(json.load(sys.stdin)['tunnels'][0]['public_url'])" 2>/dev/null || echo "Check http://localhost:4040")

    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════${NC}"
    echo -e "${GREEN}   Chat server running!${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════${NC}"
    echo ""
    echo "Local:  http://localhost:8080"
    echo "Public: $NGROK_URL"
    echo ""
    echo "Add to your website:"
    echo ""
    echo "  <script src=\"${NGROK_URL}/widget.js\""
    echo "          data-server=\"${NGROK_URL/https/wss}/ws\">"
    echo "  </script>"
    echo ""
    echo "Press Ctrl+C to stop"

    # Wait for Ctrl+C
    trap "kill $SERVER_PID $NGROK_PID 2>/dev/null" EXIT
    wait
else
    echo -e "${BLUE}Starting local server...${NC}"
    echo ""
    echo "Chat:   http://localhost:8080"
    echo "Widget: http://localhost:8080/widget.js"
    echo "Demo:   http://localhost:8080/embed-demo"
    echo ""
    echo "For public access, run: ./start.sh --ngrok"
    echo ""
    python app.py
fi
