"""Opportunity data models for empirica-outreach"""

from dataclasses import dataclass, field
from typing import Dict, Optional
from datetime import datetime
from enum import Enum


class OpportunityType(Enum):
    """Types of engagement opportunities"""
    DIRECT_MENTION = "direct_mention"
    RELEVANT_DISCUSSION = "relevant_discussion"
    PAIN_POINT_EXPRESSED = "pain_point_expressed"
    QUESTION_WE_CAN_ANSWER = "question_we_can_answer"
    COMPETITOR_DISCUSSION = "competitor_discussion"
    SCHEDULED_POST = "scheduled_post"


class OpportunityStatus(Enum):
    """Opportunity lifecycle status"""
    NEW = "new"
    REVIEWED = "reviewed"
    ENGAGED = "engaged"
    SKIPPED = "skipped"
    EXPIRED = "expired"


class ActionType(Enum):
    """Recommended actions"""
    ENGAGE = "engage"
    MONITOR = "monitor"
    SKIP = "skip"


@dataclass
class Opportunity:
    """A detected opportunity for engagement"""
    
    # Identity
    id: str
    channel_id: str
    
    # Source
    type: OpportunityType
    source_url: str
    source_content: str
    source_author: str
    source_timestamp: datetime
    
    # Assessment
    relevance_score: float  # 0-1: How relevant to our offering
    engagement_potential: float  # 0-1: Likely engagement if we respond
    urgency: float  # 0-1: Time sensitivity
    
    # Epistemic assessment
    epistemic_assessment: Dict[str, float]  # Vectors at detection time
    confidence_to_engage: float  # Should we engage?
    
    # Recommendation
    recommended_action: ActionType
    reasoning: str  # Why this recommendation
    
    # Status
    status: OpportunityStatus = OpportunityStatus.NEW
    
    # Tracking
    detected_at: datetime = field(default_factory=datetime.utcnow)
    reviewed_at: Optional[datetime] = None
    engaged_at: Optional[datetime] = None
    
    # Optional metadata
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage"""
        import json
        return {
            'id': self.id,
            'channel_id': self.channel_id,
            'type': self.type.value,
            'source_url': self.source_url,
            'source_content': self.source_content,
            'source_author': self.source_author,
            'source_timestamp': self.source_timestamp.isoformat(),
            'relevance_score': self.relevance_score,
            'engagement_potential': self.engagement_potential,
            'urgency': self.urgency,
            'epistemic_assessment': json.dumps(self.epistemic_assessment),
            'confidence_to_engage': self.confidence_to_engage,
            'recommended_action': self.recommended_action.value,
            'reasoning': self.reasoning,
            'status': self.status.value,
            'detected_at': self.detected_at.isoformat(),
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'engaged_at': self.engaged_at.isoformat() if self.engaged_at else None,
            'metadata': json.dumps(self.metadata),
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Opportunity':
        """Create from dictionary"""
        import json
        return cls(
            id=data['id'],
            channel_id=data['channel_id'],
            type=OpportunityType(data['type']),
            source_url=data['source_url'],
            source_content=data['source_content'],
            source_author=data['source_author'],
            source_timestamp=datetime.fromisoformat(data['source_timestamp']),
            relevance_score=data['relevance_score'],
            engagement_potential=data['engagement_potential'],
            urgency=data['urgency'],
            epistemic_assessment=json.loads(data['epistemic_assessment']),
            confidence_to_engage=data['confidence_to_engage'],
            recommended_action=ActionType(data['recommended_action']),
            reasoning=data['reasoning'],
            status=OpportunityStatus(data['status']),
            detected_at=datetime.fromisoformat(data['detected_at']),
            reviewed_at=datetime.fromisoformat(data['reviewed_at']) if data.get('reviewed_at') else None,
            engaged_at=datetime.fromisoformat(data['engaged_at']) if data.get('engaged_at') else None,
            metadata=json.loads(data['metadata']),
        )
