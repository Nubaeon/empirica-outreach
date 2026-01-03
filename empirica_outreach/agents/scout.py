"""Scout agent - monitors channels for opportunities"""

import uuid
from typing import List, Dict
from datetime import datetime

from empirica.core.agents import spawn_epistemic_agent, EpistemicAgentConfig
from empirica_outreach.models import (
    ChannelProfile, Opportunity, OpportunityType, ActionType, OpportunityStatus
)
from empirica_outreach.storage import OutreachDatabase


class OutreachScout:
    """
    Monitors channels for engagement opportunities.
    
    Uses spawn_epistemic_agent with outreach_scout persona for detection logic.
    Outputs opportunities with epistemic assessment.
    """
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.db = OutreachDatabase()
    
    def scan_channel(self, channel: ChannelProfile, posts: List[Dict]) -> List[Opportunity]:
        """
        Scan channel for opportunities using epistemic agent.
        
        Args:
            channel: Channel to scan
            posts: List of post dictionaries from platform API
            
        Returns:
            List of detected opportunities
        """
        
        # Build task context
        task = self._build_scan_task(channel, posts)
        
        # Spawn epistemic agent with scout persona
        config = EpistemicAgentConfig(
            session_id=self.session_id,
            task=task,
            persona_id="outreach_scout",
            investigation_path=f"scout-{channel.id}",
            parent_context=f"""
Channel: {channel.name} ({channel.platform.value})
Epistemic state: know={channel.epistemic_state.get('know', 0.5):.2f}
Audience: technical_level={channel.audience.technical_level:.2f}
Pain points: {', '.join(channel.audience.pain_points)}
"""
        )
        
        # For now, return agent result for external execution
        # In full implementation, this would execute and parse results
        result = spawn_epistemic_agent(config, execute_fn=None)
        
        # Placeholder: would parse agent output for opportunities
        # For Phase 1, we'll create opportunities directly
        opportunities = self._parse_opportunities(channel, posts)
        
        # Store opportunities
        for opp in opportunities:
            self.db.add_opportunity(opp)
        
        return opportunities
    
    def _build_scan_task(self, channel: ChannelProfile, posts: List[Dict]) -> str:
        """Build task description for scout agent"""
        return f"""Scan {channel.name} for engagement opportunities.

Analyze these {len(posts)} posts and identify:
1. Direct mentions of Empirica or related problems
2. Pain points Empirica solves (context loss, epistemic uncertainty)
3. Questions we can answer
4. Relevant technical discussions

For each opportunity, assess:
- Relevance score (0-1): How relevant to Empirica?
- Engagement potential (0-1): Likely engagement if we respond?
- Urgency (0-1): Time sensitivity?
- Confidence to engage: Should we engage?
- Recommended action: engage, monitor, or skip

Return opportunities as structured output.
"""
    
    def _parse_opportunities(self, channel: ChannelProfile, posts: List[Dict]) -> List[Opportunity]:
        """
        Parse opportunities from posts.
        
        Simplified implementation for Phase 1 - directly analyzes posts.
        In full implementation, would parse agent POSTFLIGHT output.
        """
        opportunities = []
        
        for post in posts:
            # Simple keyword matching (placeholder for agent logic)
            content = post.get('content', '').lower()
            title = post.get('title', '').lower()
            full_text = f"{title} {content}"
            
            # Check for pain points
            pain_keywords = ['context loss', 'losing context', 'forgets', 
                           'epistemic', 'uncertainty', 'don\'t know']
            has_pain = any(kw in full_text for kw in pain_keywords)
            
            # Check for questions
            is_question = '?' in full_text and len(full_text.split()) > 5
            
            # Check for AI tool mentions
            mentions_ai = any(term in full_text for term in 
                            ['claude', 'chatgpt', 'llm', 'ai agent'])
            
            # Calculate relevance
            relevance = 0.0
            if has_pain:
                relevance += 0.4
            if is_question:
                relevance += 0.3
            if mentions_ai:
                relevance += 0.3
            
            if relevance >= 0.5:
                # Create opportunity
                opp_type = (OpportunityType.PAIN_POINT_EXPRESSED if has_pain 
                           else OpportunityType.QUESTION_WE_CAN_ANSWER if is_question
                           else OpportunityType.RELEVANT_DISCUSSION)
                
                opportunity = Opportunity(
                    id=str(uuid.uuid4()),
                    channel_id=channel.id,
                    type=opp_type,
                    source_url=post.get('url', ''),
                    source_content=content[:500],  # Truncate
                    source_author=post.get('author', 'unknown'),
                    source_timestamp=post.get('timestamp', datetime.utcnow()),
                    relevance_score=relevance,
                    engagement_potential=relevance * 0.8,  # Simplified
                    urgency=0.5 if is_question else 0.3,
                    epistemic_assessment={
                        "know": channel.epistemic_state.get('know', 0.6),
                        "signal": 0.85,  # Scout's signal detection strength
                        "uncertainty": 0.4  # Scout's uncertainty
                    },
                    confidence_to_engage=relevance if relevance > 0.7 else 0.6,
                    recommended_action=(ActionType.ENGAGE if relevance > 0.7 
                                      else ActionType.MONITOR),
                    reasoning=f"Detected {opp_type.value} with relevance {relevance:.2f}",
                    status=OpportunityStatus.NEW
                )
                
                opportunities.append(opportunity)
        
        return opportunities
    
    def get_pending_opportunities(self, channel_id: str = None) -> List[Opportunity]:
        """Get opportunities pending review"""
        return self.db.list_opportunities(channel_id=channel_id, status="new")
    
    def close(self):
        self.db.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
