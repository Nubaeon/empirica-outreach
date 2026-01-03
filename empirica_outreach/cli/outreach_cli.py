"""Empirica Outreach CLI"""

import click
import json
import uuid
from pathlib import Path
from datetime import datetime

from empirica_outreach.models import (
    ChannelProfile, Platform, AudienceProfile, 
    ChannelStrategy, ChannelConstraints
)
from empirica_outreach.storage import OutreachDatabase
from empirica_outreach.agents import OutreachScout, OutreachDrafter
from empirica_outreach.integrations import RedditClient, RedditMonitor


@click.group()
def cli():
    """Empirica Outreach - Epistemic marketing and community engagement"""
    pass


@cli.command()
@click.option('--project-dir', default='.', help='Project directory')
def init(project_dir):
    """Initialize outreach project"""
    project_path = Path(project_dir)
    project_path.mkdir(parents=True, exist_ok=True)
    
    # Create config directory
    config_dir = project_path / '.empirica-outreach'
    config_dir.mkdir(exist_ok=True)
    
    # Create default config
    config = {
        "version": "1.0.0",
        "created_at": datetime.utcnow().isoformat(),
    }
    
    config_file = config_dir / 'config.json'
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    click.echo(f"✅ Initialized outreach project in {project_path}")
    click.echo(f"   Config: {config_file}")
    click.echo(f"   Database: ~/.empirica-outreach/outreach.db")


@cli.command()
@click.option('--platform', type=click.Choice(['reddit', 'twitter']), required=True)
@click.option('--name', required=True, help='Channel name (e.g., r/ClaudeAI)')
@click.option('--url', required=True, help='Channel URL')
@click.option('--output', type=click.Choice(['json', 'text']), default='text')
def channel_add(platform, name, url, output):
    """Add a channel to monitor"""
    
    # Create channel with sensible defaults
    channel = ChannelProfile(
        id=f"{platform}-{name.lower().replace('/', '-')}",
        platform=Platform(platform),
        name=name,
        url=url,
        epistemic_state={"know": 0.5, "uncertainty": 0.5},
        audience=AudienceProfile(
            technical_level=0.7,
            ai_experience=0.6,
            openness_to_tools=0.6,
            pain_points=[],
            tone_preferences=[]
        ),
        strategy=ChannelStrategy(
            message_framing="problem-led",
            entry_point="skill",
            tone="casual-technical"
        ),
        constraints=ChannelConstraints()
    )
    
    # Save to database
    db = OutreachDatabase()
    db.add_channel(channel)
    db.close()
    
    if output == 'json':
        click.echo(json.dumps({"ok": True, "channel_id": channel.id}))
    else:
        click.echo(f"✅ Channel added: {channel.name}")
        click.echo(f"   ID: {channel.id}")


@cli.command()
@click.option('--output', type=click.Choice(['json', 'text']), default='text')
def channel_list(output):
    """List all channels"""
    db = OutreachDatabase()
    channels = db.list_channels()
    db.close()
    
    if output == 'json':
        click.echo(json.dumps({
            "channels": [c.to_dict() for c in channels]
        }))
    else:
        click.echo(f"📡 Channels ({len(channels)}):")
        for channel in channels:
            click.echo(f"   • {channel.name} ({channel.platform.value})")
            click.echo(f"     ID: {channel.id}")


@cli.command()
@click.option('--channel-id', required=True, help='Channel ID')
@click.option('--session-id', help='Empirica session ID (auto-generated if not provided)')
@click.option('--limit', default=100, help='Max posts to scan')
@click.option('--output', type=click.Choice(['json', 'text']), default='text')
def scout(channel_id, session_id, limit, output):
    """Scan channel for opportunities"""
    
    if not session_id:
        session_id = f"scout-{uuid.uuid4()}"
    
    # Get channel
    db = OutreachDatabase()
    channel = db.get_channel(channel_id)
    
    if not channel:
        click.echo(f"❌ Channel not found: {channel_id}", err=True)
        return
    
    # Initialize platform client
    if channel.platform == Platform.REDDIT:
        try:
            reddit = RedditClient.from_env()
            monitor = RedditMonitor(reddit)
            
            # Extract subreddit name
            subreddit_name = channel.name.replace('r/', '')
            
            # Get posts
            posts = monitor.scan_subreddit(subreddit_name, limit=limit)
            
            # Scan with Scout
            scout_agent = OutreachScout(session_id)
            opportunities = scout_agent.scan_channel(channel, posts)
            scout_agent.close()
            
            if output == 'json':
                click.echo(json.dumps({
                    "ok": True,
                    "opportunities": [o.to_dict() for o in opportunities]
                }))
            else:
                click.echo(f"🔍 Scout Results ({channel.name}):")
                click.echo(f"   Scanned: {len(posts)} posts")
                click.echo(f"   Detected: {len(opportunities)} opportunities")
                
                for opp in opportunities:
                    click.echo(f"\n   📌 {opp.type.value}")
                    click.echo(f"      Relevance: {opp.relevance_score:.2f}")
                    click.echo(f"      Confidence: {opp.confidence_to_engage:.2f}")
                    click.echo(f"      Action: {opp.recommended_action.value}")
                    click.echo(f"      Source: {opp.source_url}")
        
        except ValueError as e:
            click.echo(f"❌ {e}", err=True)
            click.echo("   Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET", err=True)
    
    else:
        click.echo(f"❌ Platform not yet supported: {channel.platform.value}", err=True)
    
    db.close()


@cli.command()
@click.option('--opportunity-id', required=True, help='Opportunity ID')
@click.option('--session-id', help='Empirica session ID')
@click.option('--variations', default=1, help='Number of draft variations')
@click.option('--output', type=click.Choice(['json', 'text']), default='text')
def draft(opportunity_id, session_id, variations, output):
    """Create draft response to opportunity"""
    
    if not session_id:
        session_id = f"draft-{uuid.uuid4()}"
    
    db = OutreachDatabase()
    
    # Get opportunity
    opportunity = db.get_opportunity(opportunity_id)
    if not opportunity:
        click.echo(f"❌ Opportunity not found: {opportunity_id}", err=True)
        return
    
    # Get channel
    channel = db.get_channel(opportunity.channel_id)
    
    # Create draft
    drafter = OutreachDrafter(session_id)
    drafts = drafter.draft_response(opportunity, channel, variations=variations)
    drafter.close()
    
    if output == 'json':
        click.echo(json.dumps({
            "ok": True,
            "drafts": [d.to_dict() for d in drafts]
        }))
    else:
        click.echo(f"✏️  Draft Created:")
        for i, draft in enumerate(drafts, 1):
            click.echo(f"\n   Variation {i}:")
            click.echo(f"   Confidence: {draft.confidence_score:.2f}")
            click.echo(f"   Predicted engagement: {draft.predicted_engagement:.2f}")
            click.echo(f"   Status: {draft.status.value}")
            click.echo(f"\n   Body:\n   {draft.body}\n")
    
    db.close()


@cli.command()
@click.option('--status', help='Filter by status')
@click.option('--output', type=click.Choice(['json', 'text']), default='text')
def review(status, output):
    """Review pending drafts"""
    
    db = OutreachDatabase()
    drafts = db.list_drafts(status=status or "pending_review")
    db.close()
    
    if output == 'json':
        click.echo(json.dumps({
            "drafts": [d.to_dict() for d in drafts]
        }))
    else:
        click.echo(f"📝 Drafts for Review ({len(drafts)}):")
        for draft in drafts:
            click.echo(f"\n   ID: {draft.id}")
            click.echo(f"   Channel: {draft.channel_id}")
            click.echo(f"   Confidence: {draft.confidence_score:.2f}")
            click.echo(f"   Status: {draft.status.value}")
            click.echo(f"   Preview: {draft.body[:100]}...")


if __name__ == '__main__':
    cli()
