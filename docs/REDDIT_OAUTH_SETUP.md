# Reddit OAuth Setup - Manual Mode (AI as You)

**Mode:** Script app with OAuth password grant  
**User:** u/entheosoul (your account)  
**Purpose:** AI agent acts as you for outreach management

---

## Quick Answer: How to Be Smooth & Avoid Rate Limits

**Reddit allows 60 requests/minute with OAuth**

### Our Strategy:
1. **Conservative limit:** 55 req/min (leave 5 buffer)
2. **Human-like delays:** 1-2 seconds between actions
3. **Aggressive caching:** Avoid redundant API calls
4. **Exponential backoff:** Auto-retry with increasing delays on 429
5. **Circuit breaker:** Stop after 3 consecutive rate limits

**Result:** Smooth operation, no rate limit hits, indistinguishable from human browsing

---

## Implementation Plan

See full implementation details in this file for:
- OAuth app registration
- Secure credential storage
- Token management (auto-refresh)
- Rate limiting algorithm
- Caching strategy
- Error handling
