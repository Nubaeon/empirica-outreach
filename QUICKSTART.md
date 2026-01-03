# Empirica Reddit Outreach - Quick Start

**AI-Assisted Personal Outreach Management**

---

## What This Does

Helps you manage Reddit outreach with epistemic scoring:
- **Scout agent:** Finds relevant posts/discussions
- **Drafter agent:** Suggests responses with quality scoring
- **Dashboard:** Manual review before posting
- **You stay in control:** AI suggests, you decide

---

## Setup (5 minutes)

### 1. Register Reddit App

1. Go to: https://www.reddit.com/prefs/apps
2. Click "create another app..."
3. Choose **"script"** (personal use)
4. Fill in:
   - Name: `empirica-outreach-personal`
   - Redirect URI: `http://localhost:8080`
5. Save `client_id` and `client_secret`

### 2. Configure Credentials

```bash
# Copy template
cp .env.example .env

# Edit .env with your values
nano .env

# Required:
REDDIT_CLIENT_ID=abc123xyz
REDDIT_CLIENT_SECRET=secret_here
REDDIT_USERNAME=entheosoul
REDDIT_PASSWORD=your_password
REDDIT_USER_AGENT=empirica-outreach:v0.1.0 (by /u/entheosoul)
```

### 3. Test Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Test OAuth
python test_reddit_oauth.py
```

Expected output:
```
✅ Client ID: abc123...
✅ Username: u/entheosoul
✅ Mode: Authenticated (read + post)
✅ Fetched 5 posts
```

---

## Rate Limiting (Smooth Operation)

**Reddit allows 60 requests/minute with OAuth**

Our strategy ensures smooth operation:
- **55 req/min limit** (5 buffer for safety)
- **1-2s delays** between requests (human-like)
- **Thread-safe** request tracking
- **No bursting** (prevents rate limit hits)

**Result:** Indistinguishable from human browsing, zero rate limit issues

---

## Usage

### Read Mode (No Auth Required)

```python
from empirica_outreach.integrations.reddit import RedditClient

# Initialize (read-only, no username/password)
client = RedditClient(
    client_id="...",
    client_secret="...",
    user_agent="..."
)

# Fetch posts
posts = client.get_hot_posts("ArtificialIntelligence", limit=10)
```

### Post Mode (Requires Auth)

```python
# Initialize with auth
client = RedditClient(
    client_id="...",
    client_secret="...",
    user_agent="...",
    username="entheosoul",  # Your account
    password="..."
)

# Post comment (rate-limited + human-like delay)
comment = client.submit_comment(
    post_url="https://reddit.com/r/...",
    comment_text="Great point about..."
)
```

---

## Next Steps

1. ✅ Setup complete (OAuth working)
2. → Build dashboard for manual review
3. → Integrate Scout agent (finds relevant posts)
4. → Integrate Drafter agent (suggests responses)
5. → Add epistemic scoring (quality assessment)

---

## Safety Features

- **Human-in-loop:** You review everything before posting
- **Rate limiting:** Automatic, conservative (55/min)
- **Human-like delays:** 1-2s between actions
- **Epistemic scoring:** Quality filter for responses
- **No automation:** AI suggests, you decide

---

## Support

- Test script: `python test_reddit_oauth.py`
- Documentation: `docs/REDDIT_OAUTH_SETUP.md`
- Issues: https://github.com/Nubaeon/empirica-outreach/issues

---

**Status:** Phase 1 complete - OAuth + rate limiting ✅  
**Next:** Dashboard for manual posting workflow
