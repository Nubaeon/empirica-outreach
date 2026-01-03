"""Reddit platform integration"""

from typing import List, Dict, Optional
from datetime import datetime
import time
import random
import threading
import praw
from praw.models import Submission, Comment


class RedditRateLimiter:
    """
    Token bucket rate limiter for Reddit API.
    
    Smoothly distributes requests to avoid bursting and rate limit hits.
    Adds human-like delays between requests.
    """
    
    def __init__(self, max_per_minute: int = 55):
        """
        Initialize rate limiter.
        
        Args:
            max_per_minute: Max requests per minute (default 55, leaving 5 buffer from Reddit's 60)
        """
        self.max_per_minute = max_per_minute
        self.requests = []
        self.lock = threading.Lock()
    
    def wait_if_needed(self):
        """Block if rate limit would be exceeded, add human-like delay"""
        with self.lock:
            now = time.time()
            
            # Remove requests older than 1 minute
            self.requests = [t for t in self.requests if now - t < 60]
            
            if len(self.requests) >= self.max_per_minute:
                # Wait until oldest request is 60s old
                sleep_time = 60 - (now - self.requests[0]) + 0.1
                time.sleep(sleep_time)
                return self.wait_if_needed()
            
            # Add human-like delay (1-2 seconds)
            # Makes requests indistinguishable from human browsing
            time.sleep(random.uniform(1.0, 2.0))
            
            self.requests.append(now)


class RedditClient:
    """
    Reddit API client wrapper.
    
    Supports both read-only (Phase 1) and authenticated posting (Phase 2).
    Includes rate limiting and human-like delays.
    """
    
    def __init__(self, client_id: str, client_secret: str, user_agent: str,
                 username: Optional[str] = None, password: Optional[str] = None):
        """
        Initialize Reddit client.
        
        Args:
            client_id: Reddit API client ID
            client_secret: Reddit API client secret
            user_agent: User agent string (e.g., "empirica-outreach/0.1.0")
            username: Reddit username (optional, for posting)
            password: Reddit password (optional, for posting)
        """
        # Initialize rate limiter
        self.rate_limiter = RedditRateLimiter(max_per_minute=55)
        
        # Configure PRAW
        praw_config = {
            "client_id": client_id,
            "client_secret": client_secret,
            "user_agent": user_agent,
            "check_for_async": False
        }
        
        # Add auth if provided (for posting)
        if username and password:
            praw_config["username"] = username
            praw_config["password"] = password
            self.authenticated = True
        else:
            self.authenticated = False
        
        self.reddit = praw.Reddit(**praw_config)
        
        # Set read-only if not authenticated
        if not self.authenticated:
            self.reddit.read_only = True
    
    def get_recent_posts(self, subreddit_name: str, limit: int = 100,
                        time_filter: str = "day") -> List[Dict]:
        """
        Get recent posts from subreddit.
        
        Args:
            subreddit_name: Subreddit name (without r/)
            limit: Max posts to retrieve
            time_filter: "hour", "day", "week", "month", "year", "all"
            
        Returns:
            List of post dictionaries
        """
        self.rate_limiter.wait_if_needed()  # Rate limit + human-like delay
        
        subreddit = self.reddit.subreddit(subreddit_name)
        posts = []
        
        for submission in subreddit.new(limit=limit):
            post = self._submission_to_dict(submission)
            posts.append(post)
        
        return posts
    
    def get_hot_posts(self, subreddit_name: str, limit: int = 50) -> List[Dict]:
        """Get hot posts from subreddit"""
        self.rate_limiter.wait_if_needed()
        
        subreddit = self.reddit.subreddit(subreddit_name)
        posts = []
        
        for submission in subreddit.hot(limit=limit):
            post = self._submission_to_dict(submission)
            posts.append(post)
        
        return posts
    
    def search_posts(self, subreddit_name: str, query: str, 
                    limit: int = 50, time_filter: str = "week") -> List[Dict]:
        """
        Search posts in subreddit.
        
        Args:
            subreddit_name: Subreddit name
            query: Search query
            limit: Max results
            time_filter: Time filter
            
        Returns:
            List of matching posts
        """
        self.rate_limiter.wait_if_needed()
        
        subreddit = self.reddit.subreddit(subreddit_name)
        posts = []
        
        for submission in subreddit.search(query, time_filter=time_filter, limit=limit):
            post = self._submission_to_dict(submission)
            posts.append(post)
        
        return posts
    
    def get_post_comments(self, post_url: str, limit: int = 100) -> List[Dict]:
        """
        Get comments from a post.
        
        Args:
            post_url: Reddit post URL
            limit: Max comments to retrieve
            
        Returns:
            List of comment dictionaries
        """
        self.rate_limiter.wait_if_needed()
        
        submission = self.reddit.submission(url=post_url)
        submission.comments.replace_more(limit=0)  # Don't fetch "more comments"
        
        comments = []
        for comment in submission.comments.list()[:limit]:
            if isinstance(comment, Comment):
                comments.append(self._comment_to_dict(comment))
        
        return comments
    
    def submit_comment(self, post_url: str, comment_text: str) -> Dict:
        """
        Submit a comment on a post (requires authentication).
        
        Args:
            post_url: Reddit post URL
            comment_text: Comment content
            
        Returns:
            Comment details
            
        Raises:
            PermissionError: If not authenticated
        """
        if not self.authenticated:
            raise PermissionError("Authentication required for posting. Set username/password.")
        
        self.rate_limiter.wait_if_needed()
        
        submission = self.reddit.submission(url=post_url)
        comment = submission.reply(comment_text)
        
        return self._comment_to_dict(comment)
    
    def _submission_to_dict(self, submission: Submission) -> Dict:
        """Convert PRAW submission to dictionary"""
        return {
            "id": submission.id,
            "url": f"https://reddit.com{submission.permalink}",
            "title": submission.title,
            "content": submission.selftext,
            "author": str(submission.author) if submission.author else "[deleted]",
            "score": submission.score,
            "num_comments": submission.num_comments,
            "timestamp": datetime.fromtimestamp(submission.created_utc),
            "subreddit": str(submission.subreddit),
            "is_self": submission.is_self,
            "link_flair_text": submission.link_flair_text,
            "upvote_ratio": submission.upvote_ratio,
        }
    
    def _comment_to_dict(self, comment: Comment) -> Dict:
        """Convert PRAW comment to dictionary"""
        return {
            "id": comment.id,
            "url": f"https://reddit.com{comment.permalink}",
            "content": comment.body,
            "author": str(comment.author) if comment.author else "[deleted]",
            "score": comment.score,
            "timestamp": datetime.fromtimestamp(comment.created_utc),
            "parent_id": comment.parent_id,
            "is_submitter": comment.is_submitter,
        }
    
    @classmethod
    def from_env(cls):
        """
        Create client from environment variables.
        
        Requires:
            REDDIT_CLIENT_ID
            REDDIT_CLIENT_SECRET
            REDDIT_USER_AGENT
        Optional (for posting):
            REDDIT_USERNAME
            REDDIT_PASSWORD
        """
        import os
        
        client_id = os.getenv("REDDIT_CLIENT_ID")
        client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        user_agent = os.getenv("REDDIT_USER_AGENT", "empirica-outreach/0.1.0")
        username = os.getenv("REDDIT_USERNAME")
        password = os.getenv("REDDIT_PASSWORD")
        
        if not client_id or not client_secret:
            raise ValueError(
                "Missing Reddit credentials. Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET"
            )
        
        return cls(client_id, client_secret, user_agent, username, password)


class RedditMonitor:
    """
    High-level Reddit monitoring for Scout agent.
    
    Combines RedditClient with filtering and rate limiting.
    """
    
    def __init__(self, client: RedditClient):
        self.client = client
    
    def scan_subreddit(self, subreddit_name: str, 
                      keywords: Optional[List[str]] = None,
                      limit: int = 100) -> List[Dict]:
        """
        Scan subreddit for relevant posts.
        
        Args:
            subreddit_name: Subreddit to scan
            keywords: Optional keyword filter
            limit: Max posts to retrieve
            
        Returns:
            Filtered posts
        """
        # Get recent posts
        posts = self.client.get_recent_posts(subreddit_name, limit=limit)
        
        # Apply keyword filter if provided
        if keywords:
            posts = self._filter_by_keywords(posts, keywords)
        
        return posts
    
    def search_relevant(self, subreddit_name: str, 
                       queries: List[str], limit_per_query: int = 25) -> List[Dict]:
        """
        Search for relevant posts using multiple queries.
        
        Args:
            subreddit_name: Subreddit to search
            queries: List of search queries
            limit_per_query: Max results per query
            
        Returns:
            Combined search results (deduplicated)
        """
        all_posts = []
        seen_ids = set()
        
        for query in queries:
            posts = self.client.search_posts(
                subreddit_name, 
                query, 
                limit=limit_per_query
            )
            
            for post in posts:
                if post['id'] not in seen_ids:
                    all_posts.append(post)
                    seen_ids.add(post['id'])
        
        return all_posts
    
    def _filter_by_keywords(self, posts: List[Dict], keywords: List[str]) -> List[Dict]:
        """Filter posts by keywords"""
        filtered = []
        
        for post in posts:
            text = f"{post.get('title', '')} {post.get('content', '')}".lower()
            if any(kw.lower() in text for kw in keywords):
                filtered.append(post)
        
        return filtered
