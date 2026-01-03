"""Empirica Outreach - Epistemic marketing and community engagement"""

__version__ = "0.1.0"

from .models import (
    ChannelProfile, Opportunity, ContentDraft,
    Platform, OpportunityType, ContentType
)
from .storage import OutreachDatabase
from .agents import OutreachScout, OutreachDrafter
from .integrations import RedditClient, RedditMonitor

__all__ = [
    'ChannelProfile',
    'Opportunity',
    'ContentDraft',
    'Platform',
    'OpportunityType',
    'ContentType',
    'OutreachDatabase',
    'OutreachScout',
    'OutreachDrafter',
    'RedditClient',
    'RedditMonitor',
]
