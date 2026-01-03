"""Outreach database storage layer"""

import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from empirica_outreach.models import ChannelProfile, Opportunity, ContentDraft


class OutreachDatabase:
    """SQLite database for outreach data"""
    
    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            db_path = Path.home() / ".empirica-outreach" / "outreach.db"
        
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        
        self._create_tables()
    
    def _create_tables(self):
        """Create database schema"""
        
        # Channels table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS channels (
                id TEXT PRIMARY KEY,
                platform TEXT NOT NULL,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                epistemic_state TEXT NOT NULL,
                audience TEXT NOT NULL,
                strategy TEXT NOT NULL,
                constraints TEXT NOT NULL,
                engagement_metrics TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # Opportunities table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS opportunities (
                id TEXT PRIMARY KEY,
                channel_id TEXT NOT NULL,
                type TEXT NOT NULL,
                source_url TEXT NOT NULL,
                source_content TEXT NOT NULL,
                source_author TEXT NOT NULL,
                source_timestamp TEXT NOT NULL,
                relevance_score REAL NOT NULL,
                engagement_potential REAL NOT NULL,
                urgency REAL NOT NULL,
                epistemic_assessment TEXT NOT NULL,
                confidence_to_engage REAL NOT NULL,
                recommended_action TEXT NOT NULL,
                reasoning TEXT NOT NULL,
                status TEXT NOT NULL,
                detected_at TEXT NOT NULL,
                reviewed_at TEXT,
                engaged_at TEXT,
                metadata TEXT NOT NULL,
                FOREIGN KEY (channel_id) REFERENCES channels(id)
            )
        """)
        
        # Drafts table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS drafts (
                id TEXT PRIMARY KEY,
                opportunity_id TEXT,
                channel_id TEXT NOT NULL,
                content_type TEXT NOT NULL,
                title TEXT,
                body TEXT NOT NULL,
                semantic_tags TEXT NOT NULL,
                confidence_score REAL NOT NULL,
                predicted_engagement REAL NOT NULL,
                uncertainty_flags TEXT NOT NULL,
                framing TEXT NOT NULL,
                tone TEXT NOT NULL,
                status TEXT NOT NULL,
                human_feedback TEXT,
                edits_made TEXT NOT NULL,
                created_at TEXT NOT NULL,
                reviewed_at TEXT,
                posted_at TEXT,
                post_url TEXT,
                post_id TEXT,
                metadata TEXT NOT NULL,
                FOREIGN KEY (opportunity_id) REFERENCES opportunities(id),
                FOREIGN KEY (channel_id) REFERENCES channels(id)
            )
        """)
        
        # Indexes
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_opportunities_channel ON opportunities(channel_id)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_opportunities_status ON opportunities(status)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_drafts_channel ON drafts(channel_id)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_drafts_status ON drafts(status)")
        
        self.conn.commit()
    
    # Channel operations
    def add_channel(self, channel: ChannelProfile):
        """Add a channel"""
        data = channel.to_dict()
        self.conn.execute("""
            INSERT INTO channels VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data['id'], data['platform'], data['name'], data['url'],
            data['epistemic_state'], data['audience'], data['strategy'],
            data['constraints'], data['engagement_metrics'],
            data['created_at'], data['updated_at']
        ))
        self.conn.commit()
    
    def get_channel(self, channel_id: str) -> Optional[ChannelProfile]:
        """Get channel by ID"""
        cursor = self.conn.execute("SELECT * FROM channels WHERE id = ?", (channel_id,))
        row = cursor.fetchone()
        if row:
            return ChannelProfile.from_dict(dict(row))
        return None
    
    def list_channels(self) -> List[ChannelProfile]:
        """List all channels"""
        cursor = self.conn.execute("SELECT * FROM channels ORDER BY created_at DESC")
        return [ChannelProfile.from_dict(dict(row)) for row in cursor.fetchall()]
    
    def update_channel(self, channel: ChannelProfile):
        """Update channel"""
        channel.updated_at = datetime.utcnow()
        data = channel.to_dict()
        self.conn.execute("""
            UPDATE channels 
            SET platform=?, name=?, url=?, epistemic_state=?, audience=?, 
                strategy=?, constraints=?, engagement_metrics=?, updated_at=?
            WHERE id=?
        """, (
            data['platform'], data['name'], data['url'], data['epistemic_state'],
            data['audience'], data['strategy'], data['constraints'],
            data['engagement_metrics'], data['updated_at'], data['id']
        ))
        self.conn.commit()
    
    # Opportunity operations
    def add_opportunity(self, opportunity: Opportunity):
        """Add opportunity"""
        data = opportunity.to_dict()
        self.conn.execute("""
            INSERT INTO opportunities VALUES 
            (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data['id'], data['channel_id'], data['type'], data['source_url'],
            data['source_content'], data['source_author'], data['source_timestamp'],
            data['relevance_score'], data['engagement_potential'], data['urgency'],
            data['epistemic_assessment'], data['confidence_to_engage'],
            data['recommended_action'], data['reasoning'], data['status'],
            data['detected_at'], data['reviewed_at'], data['engaged_at'], data['metadata']
        ))
        self.conn.commit()
    
    def get_opportunity(self, opportunity_id: str) -> Optional[Opportunity]:
        """Get opportunity by ID"""
        cursor = self.conn.execute("SELECT * FROM opportunities WHERE id = ?", (opportunity_id,))
        row = cursor.fetchone()
        if row:
            return Opportunity.from_dict(dict(row))
        return None
    
    def list_opportunities(self, channel_id: Optional[str] = None, 
                          status: Optional[str] = None,
                          limit: Optional[int] = None) -> List[Opportunity]:
        """List opportunities with optional filters"""
        query = "SELECT * FROM opportunities WHERE 1=1"
        params = []
        
        if channel_id:
            query += " AND channel_id = ?"
            params.append(channel_id)
        if status:
            query += " AND status = ?"
            params.append(status)
        
        query += " ORDER BY detected_at DESC"
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        cursor = self.conn.execute(query, params)
        return [Opportunity.from_dict(dict(row)) for row in cursor.fetchall()]
    
    def update_opportunity_status(self, opportunity_id: str, status: str):
        """Update opportunity status"""
        self.conn.execute("""
            UPDATE opportunities SET status = ? WHERE id = ?
        """, (status, opportunity_id))
        self.conn.commit()
    
    # Draft operations
    def add_draft(self, draft: ContentDraft):
        """Add draft"""
        data = draft.to_dict()
        self.conn.execute("""
            INSERT INTO drafts VALUES 
            (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data['id'], data['opportunity_id'], data['channel_id'],
            data['content_type'], data['title'], data['body'],
            data['semantic_tags'], data['confidence_score'],
            data['predicted_engagement'], data['uncertainty_flags'],
            data['framing'], data['tone'], data['status'],
            data['human_feedback'], data['edits_made'], data['created_at'],
            data['reviewed_at'], data['posted_at'], data['post_url'],
            data['post_id'], data['metadata']
        ))
        self.conn.commit()
    
    def get_draft(self, draft_id: str) -> Optional[ContentDraft]:
        """Get draft by ID"""
        cursor = self.conn.execute("SELECT * FROM drafts WHERE id = ?", (draft_id,))
        row = cursor.fetchone()
        if row:
            return ContentDraft.from_dict(dict(row))
        return None
    
    def list_drafts(self, channel_id: Optional[str] = None,
                   status: Optional[str] = None,
                   opportunity_id: Optional[str] = None,
                   limit: Optional[int] = None) -> List[ContentDraft]:
        """List drafts with optional filters"""
        query = "SELECT * FROM drafts WHERE 1=1"
        params = []
        
        if channel_id:
            query += " AND channel_id = ?"
            params.append(channel_id)
        if status:
            query += " AND status = ?"
            params.append(status)
        if opportunity_id:
            query += " AND opportunity_id = ?"
            params.append(opportunity_id)
        
        query += " ORDER BY created_at DESC"
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        cursor = self.conn.execute(query, params)
        return [ContentDraft.from_dict(dict(row)) for row in cursor.fetchall()]
    
    def update_draft(self, draft: ContentDraft):
        """Update draft"""
        data = draft.to_dict()
        self.conn.execute("""
            UPDATE drafts 
            SET status=?, human_feedback=?, edits_made=?, reviewed_at=?,
                posted_at=?, post_url=?, post_id=?
            WHERE id=?
        """, (
            data['status'], data['human_feedback'], data['edits_made'],
            data['reviewed_at'], data['posted_at'], data['post_url'],
            data['post_id'], data['id']
        ))
        self.conn.commit()
    
    def close(self):
        """Close database connection"""
        self.conn.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
