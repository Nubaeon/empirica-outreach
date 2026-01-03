"""Content draft data models for empirica-outreach"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum


class ContentType(Enum):
    """Types of content"""
    POST = "post"
    COMMENT = "comment"
    REPLY = "reply"
    DIRECT_MESSAGE = "dm"
    ARTICLE = "article"


class DraftStatus(Enum):
    """Draft lifecycle status"""
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    POSTED = "posted"
    FAILED = "failed"


@dataclass
class EditRecord:
    """Record of an edit made to draft"""
    timestamp: datetime
    editor: str  # "human" or "agent_id"
    change_type: str  # "content", "tone", "framing"
    before: str
    after: str
    reason: Optional[str] = None


@dataclass
class ContentDraft:
    """A drafted piece of content"""
    
    # Identity
    id: str
    opportunity_id: Optional[str]  # If responding to opportunity
    channel_id: str
    
    # Content
    content_type: ContentType
    title: Optional[str] = None  # For posts that have titles
    body: str = ""
    
    # Semantic tagging
    semantic_tags: List[str] = field(default_factory=list)
    
    # Epistemic markers
    confidence_score: float = 0.0  # Drafter's confidence this will land
    predicted_engagement: float = 0.0  # Expected engagement level
    uncertainty_flags: List[str] = field(default_factory=list)  # What we're unsure about
    
    # Framing
    framing: str = "problem-led"  # problem-led, demo, technical, etc.
    tone: str = "casual-technical"
    
    # Review
    status: DraftStatus = DraftStatus.DRAFT
    human_feedback: Optional[str] = None
    edits_made: List[EditRecord] = field(default_factory=list)
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    reviewed_at: Optional[datetime] = None
    posted_at: Optional[datetime] = None
    
    # If posted
    post_url: Optional[str] = None
    post_id: Optional[str] = None
    
    # Metadata
    metadata: Dict = field(default_factory=dict)
    
    def add_edit(self, editor: str, change_type: str, before: str, after: str, reason: Optional[str] = None):
        """Record an edit"""
        self.edits_made.append(EditRecord(
            timestamp=datetime.utcnow(),
            editor=editor,
            change_type=change_type,
            before=before,
            after=after,
            reason=reason
        ))
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage"""
        import json
        return {
            'id': self.id,
            'opportunity_id': self.opportunity_id,
            'channel_id': self.channel_id,
            'content_type': self.content_type.value,
            'title': self.title,
            'body': self.body,
            'semantic_tags': json.dumps(self.semantic_tags),
            'confidence_score': self.confidence_score,
            'predicted_engagement': self.predicted_engagement,
            'uncertainty_flags': json.dumps(self.uncertainty_flags),
            'framing': self.framing,
            'tone': self.tone,
            'status': self.status.value,
            'human_feedback': self.human_feedback,
            'edits_made': json.dumps([e.__dict__ for e in self.edits_made], default=str),
            'created_at': self.created_at.isoformat(),
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'posted_at': self.posted_at.isoformat() if self.posted_at else None,
            'post_url': self.post_url,
            'post_id': self.post_id,
            'metadata': json.dumps(self.metadata),
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ContentDraft':
        """Create from dictionary"""
        import json
        
        edits_data = json.loads(data['edits_made'])
        edits = [
            EditRecord(
                timestamp=datetime.fromisoformat(e['timestamp']) if isinstance(e['timestamp'], str) else e['timestamp'],
                editor=e['editor'],
                change_type=e['change_type'],
                before=e['before'],
                after=e['after'],
                reason=e.get('reason')
            )
            for e in edits_data
        ]
        
        return cls(
            id=data['id'],
            opportunity_id=data['opportunity_id'],
            channel_id=data['channel_id'],
            content_type=ContentType(data['content_type']),
            title=data['title'],
            body=data['body'],
            semantic_tags=json.loads(data['semantic_tags']),
            confidence_score=data['confidence_score'],
            predicted_engagement=data['predicted_engagement'],
            uncertainty_flags=json.loads(data['uncertainty_flags']),
            framing=data['framing'],
            tone=data['tone'],
            status=DraftStatus(data['status']),
            human_feedback=data['human_feedback'],
            edits_made=edits,
            created_at=datetime.fromisoformat(data['created_at']),
            reviewed_at=datetime.fromisoformat(data['reviewed_at']) if data.get('reviewed_at') else None,
            posted_at=datetime.fromisoformat(data['posted_at']) if data.get('posted_at') else None,
            post_url=data['post_url'],
            post_id=data['post_id'],
            metadata=json.loads(data['metadata']),
        )
