"""API routes for outreach dashboard"""

from datetime import datetime
from flask import Blueprint, jsonify, request, render_template
from empirica_outreach.storage import OutreachDatabase
from empirica_outreach.agents import OutreachScout, OutreachDrafter
from empirica_outreach.integrations import RedditClient, RedditMonitor
from empirica_outreach.models import (
    Platform, ChannelProfile, AudienceProfile,
    ChannelStrategy, ChannelConstraints, EngagementMetrics
)
import uuid

bp = Blueprint('outreach', __name__)


@bp.route('/', methods=['GET'])
def dashboard():
    """Serve dashboard HTML"""
    return render_template('dashboard.html')


@bp.route('/channels', methods=['GET'])
def list_channels():
    """List all channels"""
    db = OutreachDatabase()
    channels = db.list_channels()
    db.close()
    
    return jsonify({
        "ok": True,
        "channels": [c.to_dict() for c in channels]
    })


@bp.route('/opportunities', methods=['GET'])
def list_opportunities():
    """
    List opportunities with filters.
    
    Query params:
        channel_id: Filter by channel
        status: Filter by status (new, reviewed, engaged, skipped)
        limit: Max results (default 50)
    """
    db = OutreachDatabase()
    
    channel_id = request.args.get('channel_id')
    status = request.args.get('status')
    limit = int(request.args.get('limit', 50))
    
    opportunities = db.list_opportunities(
        channel_id=channel_id,
        status=status,
        limit=limit
    )
    db.close()
    
    return jsonify({
        "ok": True,
        "opportunities": [o.to_dict() for o in opportunities],
        "count": len(opportunities)
    })


@bp.route('/opportunities/<opportunity_id>', methods=['GET'])
def get_opportunity(opportunity_id):
    """Get single opportunity"""
    db = OutreachDatabase()
    opportunity = db.get_opportunity(opportunity_id)
    db.close()
    
    if not opportunity:
        return jsonify({
            "ok": False,
            "error": "not_found",
            "message": "Opportunity not found"
        }), 404
    
    return jsonify({
        "ok": True,
        "opportunity": opportunity.to_dict()
    })


@bp.route('/drafts', methods=['GET'])
def list_drafts():
    """
    List drafts with filters.
    
    Query params:
        opportunity_id: Filter by opportunity
        status: Filter by status (pending_review, approved, rejected, posted)
        limit: Max results (default 50)
    """
    db = OutreachDatabase()
    
    opportunity_id = request.args.get('opportunity_id')
    status = request.args.get('status', 'pending_review')
    limit = int(request.args.get('limit', 50))
    
    drafts = db.list_drafts(
        opportunity_id=opportunity_id,
        status=status,
        limit=limit
    )
    db.close()
    
    return jsonify({
        "ok": True,
        "drafts": [d.to_dict() for d in drafts],
        "count": len(drafts)
    })


@bp.route('/drafts/<draft_id>', methods=['GET'])
def get_draft(draft_id):
    """Get single draft"""
    db = OutreachDatabase()
    draft = db.get_draft(draft_id)
    db.close()
    
    if not draft:
        return jsonify({
            "ok": False,
            "error": "not_found",
            "message": "Draft not found"
        }), 404
    
    return jsonify({
        "ok": True,
        "draft": draft.to_dict()
    })


@bp.route('/drafts/<draft_id>/approve', methods=['POST'])
def approve_draft(draft_id):
    """
    Approve a draft for posting.
    
    Body:
        session_id: Optional Empirica session ID
        feedback: Optional human feedback
    """
    data = request.get_json() or {}
    session_id = data.get('session_id', f"approve-{uuid.uuid4()}")
    feedback = data.get('feedback', '')
    
    db = OutreachDatabase()
    draft = db.get_draft(draft_id)
    
    if not draft:
        db.close()
        return jsonify({
            "ok": False,
            "error": "not_found",
            "message": "Draft not found"
        }), 404
    
    # Update status
    draft.status = "approved"
    draft.human_review_feedback = feedback
    db.update_draft(draft)
    db.close()
    
    return jsonify({
        "ok": True,
        "draft_id": draft_id,
        "status": "approved",
        "message": "Draft approved"
    })


@bp.route('/drafts/<draft_id>/reject', methods=['POST'])
def reject_draft(draft_id):
    """
    Reject a draft.
    
    Body:
        session_id: Optional Empirica session ID
        feedback: Required rejection reason
    """
    data = request.get_json() or {}
    session_id = data.get('session_id', f"reject-{uuid.uuid4()}")
    feedback = data.get('feedback', 'Rejected by human')
    
    db = OutreachDatabase()
    draft = db.get_draft(draft_id)
    
    if not draft:
        db.close()
        return jsonify({
            "ok": False,
            "error": "not_found",
            "message": "Draft not found"
        }), 404
    
    # Update status
    draft.status = "rejected"
    draft.human_review_feedback = feedback
    db.update_draft(draft)
    db.close()
    
    return jsonify({
        "ok": True,
        "draft_id": draft_id,
        "status": "rejected",
        "message": "Draft rejected"
    })


@bp.route('/drafts/<draft_id>/edit', methods=['POST'])
def edit_draft(draft_id):
    """
    Edit a draft.
    
    Body:
        body: New draft body
        session_id: Optional Empirica session ID
    """
    data = request.get_json() or {}
    new_body = data.get('body')
    session_id = data.get('session_id', f"edit-{uuid.uuid4()}")
    
    if not new_body:
        return jsonify({
            "ok": False,
            "error": "bad_request",
            "message": "Missing 'body' field"
        }), 400
    
    db = OutreachDatabase()
    draft = db.get_draft(draft_id)
    
    if not draft:
        db.close()
        return jsonify({
            "ok": False,
            "error": "not_found",
            "message": "Draft not found"
        }), 404
    
    # Track edit
    if not draft.edit_history:
        draft.edit_history = []
    
    draft.edit_history.append({
        "version": len(draft.edit_history) + 1,
        "previous_body": draft.body,
        "timestamp": str(uuid.uuid4())  # Simplified
    })
    
    draft.body = new_body
    draft.human_edited = True
    db.update_draft(draft)
    db.close()
    
    return jsonify({
        "ok": True,
        "draft_id": draft_id,
        "message": "Draft updated",
        "edit_count": len(draft.edit_history)
    })


@bp.route('/scout/run', methods=['POST'])
def run_scout():
    """
    Run Scout agent on a channel.
    
    Body:
        channel_id: Channel to scan
        session_id: Optional Empirica session ID
        limit: Max posts to scan (default 100)
    """
    data = request.get_json() or {}
    channel_id = data.get('channel_id')
    session_id = data.get('session_id', f"scout-{uuid.uuid4()}")
    limit = data.get('limit', 100)
    
    if not channel_id:
        return jsonify({
            "ok": False,
            "error": "bad_request",
            "message": "Missing 'channel_id' field"
        }), 400
    
    db = OutreachDatabase()
    channel = db.get_channel(channel_id)
    
    if not channel:
        db.close()
        return jsonify({
            "ok": False,
            "error": "not_found",
            "message": "Channel not found"
        }), 404
    
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
            scout = OutreachScout(session_id)
            opportunities = scout.scan_channel(channel, posts)
            scout.close()
            
            db.close()
            
            return jsonify({
                "ok": True,
                "channel_id": channel_id,
                "posts_scanned": len(posts),
                "opportunities_detected": len(opportunities),
                "opportunities": [o.to_dict() for o in opportunities]
            })
        
        except ValueError as e:
            db.close()
            return jsonify({
                "ok": False,
                "error": "configuration_error",
                "message": str(e)
            }), 500
    
    else:
        db.close()
        return jsonify({
            "ok": False,
            "error": "not_implemented",
            "message": f"Platform {channel.platform.value} not yet supported"
        }), 501


@bp.route('/stats', methods=['GET'])
def get_stats():
    """Get dashboard statistics"""
    db = OutreachDatabase()
    
    # Count totals
    all_channels = db.list_channels()
    all_opportunities = db.list_opportunities(limit=10000)
    all_drafts = db.list_drafts(status=None, limit=10000)
    
    pending_drafts = [d for d in all_drafts if d.status == "pending_review"]
    approved_drafts = [d for d in all_drafts if d.status == "approved"]
    
    db.close()
    
    return jsonify({
        "ok": True,
        "stats": {
            "channels": len(all_channels),
            "opportunities": {
                "total": len(all_opportunities),
                "new": len([o for o in all_opportunities if o.status == "new"])
            },
            "drafts": {
                "total": len(all_drafts),
                "pending_review": len(pending_drafts),
                "approved": len(approved_drafts)
            }
        }
    })


@bp.route('/manual/submit', methods=['POST'])
def manual_submit():
    """
    Accept manual post input (URL or text).
    
    Body:
        url: Optional URL to fetch
        text: Optional raw text
        platform: Platform (reddit, hackernews, twitter)
        session_id: Optional Empirica session ID
    """
    data = request.get_json() or {}
    url = data.get('url')
    text = data.get('text')
    platform = data.get('platform', 'reddit')
    session_id = data.get('session_id', f"manual-{uuid.uuid4()}")
    
    if not url and not text:
        return jsonify({
            "ok": False,
            "error": "bad_request",
            "message": "Must provide either 'url' or 'text'"
        }), 400
    
    db = OutreachDatabase()
    
    try:
        # If URL provided, try to fetch content
        content = text
        if url:
            # TODO: Implement URL fetching with BeautifulSoup/requests
            # For now, use the text field or create placeholder
            content = text or f"Content from {url}"
        
        # Create a pseudo-channel for manual input
        from empirica_outreach import models as channel
        
        platform_enum = Platform(platform.lower())
        channel = ChannelProfile(
            id=f"manual-{platform}",
            platform=platform_enum,
            name=f"Manual {platform.title()} Input",
            url=url or "manual",
            epistemic_state={"know": 0.5, "uncertainty": 0.5},
            audience=AudienceProfile(
                technical_level=0.7,
                ai_experience=0.7,
                openness_to_tools=0.7,
                pain_points=[],
                interests=[],
                turn_offs=[],
                tone_preferences=[],
                confidence=0.5
            ),
            strategy=ChannelStrategy(
                message_framing="problem-led",
                entry_point="skill",
                tone="technical",
                best_times=[],
                frequency_limit="unlimited",
                avoid=[]
            ),
            constraints=ChannelConstraints(
                min_confidence_to_post=0.5,
                min_know_to_engage=0.5,
                max_posts_per_period=999,
                period_days=1,
                requires_human_approval=True,
                auto_respond_enabled=False,
                auto_respond_confidence=1.0
            ),
            engagement_metrics=EngagementMetrics(
                total_posts=0,
                total_reactions=0,
                total_comments=0,
                avg_engagement_rate=0.0,
                best_performer_id=None,
                best_performer_score=0.0
            )
        )
        
        # Create pseudo-post
        post = {
            "id": str(uuid.uuid4()),
            "title": "Manual Input",
            "body": content,
            "url": url,
            "author": "manual",
            "created": datetime.now().isoformat(),
            "score": 0,
            "num_comments": 0
        }
        
        # Score with Scout agent
        scout = OutreachScout(session_id)
        opportunities = scout.scan_channel(channel, [post])
        scout.close()
        
        db.close()
        
        # Return scoring results
        if opportunities:
            opp = opportunities[0].to_dict()
            return jsonify({
                "ok": True,
                "scored": True,
                "opportunity": opp,
                "scores": {
                    "relevance": opp.get('relevance_score', 0),
                    "engagement": opp.get('engagement_potential', 0),
                    "urgency": opp.get('urgency', 0)
                },
                "message": "Post scored successfully"
            })
        else:
            return jsonify({
                "ok": True,
                "scored": False,
                "message": "No opportunities detected (low relevance)"
            })
    
    except Exception as e:
        db.close()
        return jsonify({
            "ok": False,
            "error": "internal_server_error",
            "message": str(e)
        }), 500


@bp.route('/score', methods=['POST'])
def score_content():
    """
    Score content for epistemic quality (standalone endpoint).
    
    Body:
        text: Content to score
        platform: Platform context (optional)
    """
    data = request.get_json() or {}
    text = data.get('text')
    platform = data.get('platform', 'generic')
    
    if not text:
        return jsonify({
            "ok": False,
            "error": "bad_request",
            "message": "Missing 'text' field"
        }), 400
    
    # Simple epistemic scoring
    from empirica_outreach import models as channel
    
    # Keyword matching
    keywords = [
        'empirica', 'epistemic', 'uncertainty', 'confidence',
        'calibration', 'alignment', 'grounding', 'self-aware',
        'context', 'know', 'guess', 'trust'
    ]
    
    text_lower = text.lower()
    keyword_matches = sum(1 for kw in keywords if kw in text_lower)
    relevance = min(keyword_matches / 5.0, 1.0)  # Normalize
    
    # Quality indicators
    has_question = '?' in text
    has_technical = any(term in text_lower for term in [
        'implement', 'algorithm', 'architecture', 'api', 'system'
    ])
    has_pain_point = any(term in text_lower for term in [
        'problem', 'issue', 'challenge', 'difficult', 'struggle'
    ])
    
    quality = (
        (0.3 if has_question else 0) +
        (0.4 if has_technical else 0) +
        (0.3 if has_pain_point else 0)
    )
    
    # Engagement potential
    engagement = (relevance * 0.6) + (quality * 0.4)
    
    return jsonify({
        "ok": True,
        "scores": {
            "relevance": round(relevance, 2),
            "quality": round(quality, 2),
            "engagement": round(engagement, 2),
            "keyword_matches": keyword_matches
        },
        "indicators": {
            "has_question": has_question,
            "has_technical": has_technical,
            "has_pain_point": has_pain_point
        },
        "message": "Content scored"
    })
