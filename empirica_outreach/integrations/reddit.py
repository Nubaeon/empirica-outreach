"""Reddit platform integration"""

from typing import List, Dict, Optional
from datetime import datetime
import praw
from praw.models import Submission, Comment


class RedditClient:
    """
    Reddit API client wrapper.
    
    Uses PRAW for read-only operations in Phase 1.
    Provides subreddit monitoring for Scout agent.
    """
    
    def __init__(self, client_id: str, client_secret: str, user_agent: str):
        """
        Initialize Reddit client.
        
        Args:
            client_id: Reddit API client ID
            client_secret: Reddit API client secret
            user_agent: User agent string (e.g., "empirica-outreach/0.1.0")
        """
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
            # Read-only mode (no username/password needed)
            check_for_async=False
        )
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
        subreddit = self.reddit.subreddit(subreddit_name)
        posts = []
        
        for submission in subreddit.new(limit=limit):
            post = self._submission_to_dict(submission)
            posts.append(post)
        
        return posts
    
    def get_hot_posts(self, subreddit_name: str, limit: int = 50) -> List[Dict]:
        """Get hot posts from subreddit"""
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
        submission = self.reddit.submission(url=post_url)
        submission.comments.replace_more(limit=0)  # Don't fetch "more comments"
        
        comments = []
        for comment in submission.comments.list()[:limit]:
            if isinstance(comment, Comment):
                comments.append(self._comment_to_dict(comment))
        
        return comments
    
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
        """
        import os
        
        client_id = os.getenv("REDDIT_CLIENT_ID")
        client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        user_agent = os.getenv("REDDIT_USER_AGENT", "empirica-outreach/0.1.0")
        
        if not client_id or not client_secret:
            raise ValueError(
                "Missing Reddit credentials. Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET"
            )
        
        return cls(client_id, client_secret, user_agent)


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
