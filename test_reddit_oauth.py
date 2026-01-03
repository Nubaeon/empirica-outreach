#!/usr/bin/env python3
"""Test Reddit OAuth setup and rate limiting"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import Reddit client
sys.path.insert(0, os.path.dirname(__file__))
from empirica_outreach.integrations.reddit import RedditClient


def test_oauth_setup():
    """Test OAuth authentication"""
    print("=" * 60)
    print("REDDIT OAUTH TEST")
    print("=" * 60)
    print()
    
    # Check credentials
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    username = os.getenv("REDDIT_USERNAME")
    password = os.getenv("REDDIT_PASSWORD")
    
    if not client_id or not client_secret:
        print("❌ Missing credentials in .env file")
        print()
        print("Please copy .env.example to .env and fill in:")
        print("1. REDDIT_CLIENT_ID")
        print("2. REDDIT_CLIENT_SECRET")
        print("3. REDDIT_USERNAME (optional, for posting)")
        print("4. REDDIT_PASSWORD (optional, for posting)")
        print()
        print("Register app at: https://www.reddit.com/prefs/apps")
        return False
    
    print(f"✅ Client ID: {client_id[:8]}...")
    print(f"✅ Client Secret: {'*' * 12}")
    
    if username and password:
        print(f"✅ Username: u/{username}")
        print(f"✅ Password: {'*' * len(password)}")
        print(f"✅ Mode: Authenticated (read + post)")
    else:
        print(f"⚠️  Mode: Read-only (no username/password)")
    
    print()
    
    # Create client
    try:
        client = RedditClient.from_env()
        print("✅ Reddit client initialized")
        print()
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        return False
    
    # Test API call
    try:
        print("Testing API call: Fetching r/ArtificialIntelligence hot posts...")
        print("(Note: This will have 1-2 second delay due to rate limiting)")
        print()
        
        posts = client.get_hot_posts("ArtificialIntelligence", limit=5)
        
        print(f"✅ Fetched {len(posts)} posts")
        print()
        
        print("Sample posts:")
        for i, post in enumerate(posts[:3], 1):
            print(f"{i}. {post['title'][:60]}...")
            print(f"   Score: {post['score']} | Comments: {post['num_comments']}")
            print()
        
    except Exception as e:
        print(f"❌ API call failed: {e}")
        return False
    
    # Test authenticated features
    if client.authenticated:
        print("=" * 60)
        print("AUTHENTICATED MODE AVAILABLE")
        print("=" * 60)
        print()
        print("✅ You can now use submit_comment() to post")
        print("✅ Rate limited to 55 requests/minute")
        print("✅ Human-like 1-2s delays between actions")
        print()
    else:
        print("=" * 60)
        print("READ-ONLY MODE")
        print("=" * 60)
        print()
        print("⚠️  Add REDDIT_USERNAME and REDDIT_PASSWORD to .env for posting")
        print()
    
    print("=" * 60)
    print("RATE LIMITING INFO")
    print("=" * 60)
    print()
    print("✅ Conservative: 55 req/min (leaving 5 buffer)")
    print("✅ Human-like: 1-2s random delays")
    print("✅ Thread-safe: Multiple operations won't conflict")
    print("✅ Smooth: No bursting, no rate limit hits")
    print()
    
    return True


if __name__ == "__main__":
    success = test_oauth_setup()
    sys.exit(0 if success else 1)
