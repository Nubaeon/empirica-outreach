"""Channel data models for empirica-outreach"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum


class Platform(Enum):
    """Supported platforms"""
    REDDIT = "reddit"
    TWITTER = "twitter"
    HACKERNEWS = "hackernews"
    DEVTO = "devto"
    EMAIL = "email"


@dataclass
class AudienceProfile:
    """What we know about a channel's audience"""
    
    # Technical understanding
    technical_level: float  # 0-1
    ai_experience: float  # 0-1
    openness_to_tools: float  # 0-1
    
    # Domain knowledge
    pain_points: List[str] = field(default_factory=list)
    interests: List[str] = field(default_factory=list)
    turn_offs: List[str] = field(default_factory=list)
    
    # Communication preferences
    tone_preferences: List[str] = field(default_factory=list)  # ["technical", "no-hype", etc.]
    
    # Confidence in this profile
    confidence: float = 0.5  # How sure are we?


@dataclass
class ChannelStrategy:
    """How to engage this channel"""
    
    message_framing: str  # "problem-led", "demo-first", "technical-deep-dive"
    entry_point: str  # What to offer first (skill, CLI, docs)
    tone: str  # "casual-technical", "formal", "conversational"
    
    # Timing
    best_times: List[str] = field(default_factory=list)  # When to post
    frequency_limit: str = "1 per week"  # Rate limit
    
    # Constraints
    avoid: List[str] = field(default_factory=list)  # What not to do


@dataclass
class ChannelConstraints:
    """Hard limits for this channel"""
    
    min_confidence_to_post: float = 0.70
    min_know_to_engage: float = 0.60
    max_posts_per_period: int = 2
    period_days: int = 7
    
    requires_human_approval: bool = True
    auto_respond_enabled: bool = False
    auto_respond_confidence: float = 0.85


@dataclass
class EngagementMetrics:
    """Historical engagement metrics"""
    
    total_posts: int = 0
    total_reactions: int = 0
    total_comments: int = 0
    avg_engagement_rate: float = 0.0
    
    best_performer_id: Optional[str] = None
    best_performer_score: float = 0.0


@dataclass
class ChannelProfile:
    """Complete profile for a channel"""
    
    # Identity
    id: str  # e.g., "reddit-r-claudeai"
    platform: Platform
    name: str  # Human readable
    url: str
    
    # Epistemic state (reuses core EpistemicVectors structure)
    epistemic_state: Dict[str, float]  # know, uncertainty, context, etc.
    
    # Audience understanding
    audience: AudienceProfile
    
    # Strategy
    strategy: ChannelStrategy
    
    # Constraints
    constraints: ChannelConstraints
    
    # Historical performance
    engagement_metrics: EngagementMetrics = field(default_factory=EngagementMetrics)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage"""
        import json
        return {
            'id': self.id,
            'platform': self.platform.value,
            'name': self.name,
            'url': self.url,
            'epistemic_state': json.dumps(self.epistemic_state),
            'audience': json.dumps(self.audience.__dict__),
            'strategy': json.dumps(self.strategy.__dict__),
            'constraints': json.dumps(self.constraints.__dict__),
            'engagement_metrics': json.dumps(self.engagement_metrics.__dict__),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ChannelProfile':
        """Create from dictionary"""
        import json
        return cls(
            id=data['id'],
            platform=Platform(data['platform']),
            name=data['name'],
            url=data['url'],
            epistemic_state=json.loads(data['epistemic_state']),
            audience=AudienceProfile(**json.loads(data['audience'])),
            strategy=ChannelStrategy(**json.loads(data['strategy'])),
            constraints=ChannelConstraints(**json.loads(data['constraints'])),
            engagement_metrics=EngagementMetrics(**json.loads(data['engagement_metrics'])),
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
        )
