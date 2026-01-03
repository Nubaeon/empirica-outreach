# Empirica Outreach

**Epistemic Quality Matching for Reddit Help Communities**

A personal productivity tool that helps domain experts find high-quality questions to answer across Reddit's help communities. Built with transparency and epistemic rigor.

## 🎯 Purpose

This tool addresses a real problem in Reddit's help ecosystem: **quality questions get buried in noise**. Domain experts waste time scrolling; askers don't get expert attention.

**Solution:** Epistemic quality scoring surfaces relevant, well-formulated questions to experts, improving answer quality for everyone.

## ⚠️ What This Is NOT

- **NOT an AI training system** - No ML model training on Reddit data
- **NOT automated posting** - Every response manually reviewed and posted by human
- **NOT a bot** - Human-driven tool with API assistance for discovery only
- **NOT commercial** - Open source, helping community quality
- **NOT data mining for resale** - Personal productivity tool (like browser cache)

## ✅ What This IS

- **Human-augmented help** - API assists human expert in finding quality questions
- **Platform quality improvement** - Benefits Reddit's help communities
- **Transparent & compliant** - Full disclosure, working WITH Reddit
- **Open source** - You're reading the code right now

## 🏗️ Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Reddit    │────▶│    Scout     │────▶│   Human     │
│     API     │     │    Agent     │     │   Review    │
│ (Read Only) │     │  (Scoring)   │     │  Dashboard  │
└─────────────┘     └──────────────┘     └─────────────┘
                                                │
                                                ▼
                                          ┌─────────────┐
                                          │   Manual    │
                                          │  Response   │
                                          │  (by human) │
                                          └─────────────┘
```

**Human-in-loop at every step:**
1. API monitors help subreddits (read-only)
2. Scout agent scores posts for epistemic quality
3. **Human reviews** scored posts
4. **Human writes** response (no AI generation)
5. **Human posts** response manually

## 📊 Epistemic Scoring

Posts are analyzed for quality markers:
- **Well-formulated questions** (clear, specific)
- **Technical depth** indicators
- **Epistemic clarity** (distinguishes fact from speculation)
- **Novelty** (avoids duplicates)

**Not scoring users** - analyzing content quality only.

## 🗄️ Data Handling

**Local caching only** - Like any productivity tool:
- Caches posts you might respond to (like browser cache)
- Stores your drafted responses
- No sharing, selling, or AI training
- Equivalent to Reddit's "Save Post" feature

**What we store:**
- Post IDs (duplicate detection)
- Post content (personal cache)
- Your drafted responses
- Your engagement history

**What we DON'T do:**
- ❌ Share data with third parties
- ❌ Train AI models on Reddit data
- ❌ Profile or re-identify users
- ❌ Commercialize Reddit content

## 🚀 Setup

### Prerequisites
- Python 3.11+
- Reddit API credentials (after approval)
- Empirica framework (for epistemic agents)

### Installation

```bash
# Clone repo
git clone https://github.com/Nubaeon/empirica-outreach.git
cd empirica-outreach

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export REDDIT_CLIENT_ID="your_client_id"
export REDDIT_CLIENT_SECRET="your_client_secret"
export REDDIT_USER_AGENT="EmpricaOutreach/1.0"

# Run API
python -m empirica_outreach.api.app
```

### Usage

```bash
# Start dashboard (localhost:8001)
python run_api.py

# Manual input (copy-paste workflow)
curl -X POST http://localhost:8001/api/v1/outreach/manual/submit \
  -H "Content-Type: application/json" \
  -d '{"text": "How do I track epistemic uncertainty in my AI system?", "platform": "reddit"}'

# View scored opportunities
curl http://localhost:8001/api/v1/outreach/opportunities
```

## 📝 API Endpoints

- `GET /health` - Health check
- `GET /api/v1/outreach/stats` - Dashboard statistics
- `GET /api/v1/outreach/opportunities` - Scored posts
- `POST /api/v1/outreach/manual/submit` - Submit URL/text for scoring
- `POST /api/v1/outreach/score` - Standalone epistemic scoring

## 🔒 Reddit API Compliance

This tool is designed for **Reddit API approval** with full compliance:

- ✅ **Responsible Builder Policy** compliant
- ✅ **Human-supervised** (not automated bot)
- ✅ **Read-only access** (write access manual)
- ✅ **Rate limited** (60 req/min max)
- ✅ **Transparent** (open source)
- ✅ **Single user** (personal productivity)

See: [Reddit Responsible Builder Policy](https://support.reddithelp.com/hc/en-us/articles/42728983564564-Responsible-Builder-Policy)

## 🤝 Target Subreddits

Help communities where epistemic quality matters:
- r/MachineLearning
- r/learnprogramming  
- r/AskScience
- r/ArtificialIntelligence
- r/ClaudeAI
- ...and more (see config)

## 📖 Related Projects

- **[Empirica](https://github.com/yourusername/empirica)** - Epistemic self-awareness framework for AI agents
- Built with [Empirica CASCADE workflow](https://github.com/yourusername/empirica/docs/CASCADE_WORKFLOW.md)

## 📄 License

MIT License - See [LICENSE](LICENSE)

## 🙏 Acknowledgments

Built to improve Reddit's help communities through transparent, human-supervised epistemic quality matching.

**Doing this the RIGHT way** - Requesting proper API access instead of using OAuth workarounds, because AI-assisted participation should be transparent and beneficial to platforms.

---

**Questions?** Open an issue or reach out to u/entheosoul
