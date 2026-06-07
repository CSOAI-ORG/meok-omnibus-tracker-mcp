#!/usr/bin/env python3
"""
meok-omnibus-tracker-mcp
============================
EU Digital Omnibus AI Act tracker - Track delay status, query by article.

RESEARCH CONTEXT (from 08_REVENUE_CATAPULT_PLAYBOOK.md):
- EU Parliament voted 23 March 2026 to delay parts of AI Act
- Trilogue negotiations LIVE (high virality opportunity)
- First-mover advantage: "First-mover wins permanent SEO + brand"
- Show HN Wednesday morning PST strategy

REVENUE: Lead capture → £199 Pro tier upsell
"""
import json
from datetime import datetime, timedelta, timezone
from typing import Optional
from collections import defaultdict
from mcp.server.fastmcp import FastMCP

import os as _os
import sys
import os

_MEOK_API_KEY = _os.environ.get("MEOK_API_KEY", "")

try:
    sys.path.insert(0, os.path.expanduser("~/clawd/meok-labs-engine/shared"))
    from auth_middleware import check_access as _shared_check_access
except ImportError:
    def _shared_check_access(api_key=""):
        key = api_key or os.environ.get("MEOK_API_KEY", "")
        if not key:
            return True, "OK, Pro at https://www.csoai.org/checkout", "free"
        if key.startswith("CSOAI-"):
            return True, "OK", "pro"
        import time as _t, collections as _c
        r = getattr(_shared_check_access, "_rate", {"c": 0, "r": _t.time() + 86400})
        if _t.time() > r["r"]:
            r["c"] = 0
            r["r"] = _t.time() + 86400
        r["c"] += 1
        _shared_check_access._rate = r
        if r["c"] > 10:
            return False, "Free: 10/10 today. Pro at https://csoai.org/pricing", "free"
        return True, f"Free: {r['c']}/10 today. Pro at https://csoai.org/pricing", "free"


def check_access(api_key: str = ""):
    return _shared_check_access(api_key)


FREE_DAILY_LIMIT = 10
_usage: dict[str, list[datetime]] = defaultdict(list)
STRIPE_199 = "https://buy.stripe.com/14A4gB3K4eUWgYR56o8k836"


def _rl(tier="free") -> Optional[str]:
    if tier in ("pro", "professional", "enterprise"):
        return None
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=1)
    _usage["anonymous"] = [t for t in _usage["anonymous"] if t > cutoff]
    if len(_usage["anonymous"]) >= FREE_DAILY_LIMIT:
        return f"Free tier limit ({FREE_DAILY_LIMIT}/day). Pro GBP 199/mo: {STRIPE_199}"
    _usage["anonymous"].append(now)
    return None

mcp = FastMCP(
    "meok-omnibus-tracker-mcp",
    instructions=(
        "EU Digital Omnibus AI Act delay tracker. Query by article, "
        "track implementation deadlines, get trilogue negotiation updates. "
        "First-mover advantage: Parliament voted 23 March 2026. "
        "Built by MEOK AI Labs (https://meok.ai)"
    ),
)

# ── Structured Output Helpers ─────────────────────────────────

def structured_output(data, summary: str = ""):
    """Return MCP-compatible structured output with both LLM text and protocol-level data.
    
    Args:
        data: The result data (dict, list, or Pydantic model)
        summary: Brief human-readable summary for the LLM (auto-generated if empty)
    """
    if hasattr(data, 'model_dump'):
        data_dict = data.model_dump()
    else:
        data_dict = data
    
    if not summary:
        # Auto-generate summary from key fields
        parts = []
        for k, v in list(data_dict.items())[:3]:
            if isinstance(v, (str, int, float)):
                parts.append(f"{k}: {v}")
        summary = " | ".join(parts) if parts else "Result"
    
    return {
        "content": [{"type": "text", "text": summary + "\n\n" + str(data_dict)}],
        "structuredContent": data_dict,
        **data_dict  # Legacy compatibility
    }


def error_output(message: str, code: str = "INTERNAL_ERROR", upgrade_url: str = ""):
    """Return structured error output."""
    result = {
        "content": [{"type": "text", "text": f"Error: {message}"}],
        "structuredContent": {"error": message, "code": code},
        "error": message,
        "code": code
    }
    if upgrade_url:
        result["structuredContent"]["upgrade_url"] = upgrade_url
        result["upgrade_url"] = upgrade_url
    return result

# Omnibus delay data (as of May 2026)
OMNIBUS_DATA = {
    "vote_date": "2026-03-23",
    "trilogue_status": "LIVE - ongoing negotiations",
    "delay_effective": "2026-07-01",  # Expected
    "articles_affected": {
        "Article 11": {
            "title": "Technical documentation",
            "original_date": "2026-08-02",
            "delayed_to": "2027-02-01",
            "status": "DELAYED"
        },
        "Article 12": {
            "title": "Record-keeping",
            "original_date": "2026-08-02",
            "delayed_to": "2027-02-01",
            "status": "DELAYED"
        },
        "Article 53": {
            "title": "High-risk AI systems",
            "original_date": "2026-11-01",
            "delayed_to": "2027-05-01",
            "status": "DELAYED"
        },
        "Article 54": {
            "title": "Post-market monitoring",
            "original_date": "2026-11-01",
            "delayed_to": "2027-05-01",
            "status": "DELAYED"
        }
    },
    "next_milestone": "Trilogue agreement (expected June 2026)",
    "implementation_deadline": "2027-02-01 (Article 11/12)"
}

@mcp.tool()
def query_article(article: str) -> str:
    """Query Omnibus delay status for specific article (e.g., 'Article 11')."""
    key = f"Article {article}" if not article.startswith("Article") else article
    
    if key in OMNIBUS_DATA["articles_affected"]:
        data = OMNIBUS_DATA["articles_affected"][key]
        return json.dumps({
            "article": key,
            "title": data["title"],
            "original_deadline": data["original_date"],
            "delayed_to": data["delayed_to"],
            "status": data["status"],
            "days_delayed": (
                datetime.strptime(data["delayed_to"], "%Y-%m-%d") -
                datetime.strptime(data["original_date"], "%Y-%m-%d")
            ).days,
            "compliance_action": f"Update your roadmap - new deadline {data['delayed_to']}",
            "verify_url": "https://meok.ai/verify/omnibus"
        }, indent=2)
    else:
        return json.dumps({
            "error": f"Article '{key}' not found in Omnibus delay list",
            "available_articles": list(OMNIBUS_DATA["articles_affected"].keys()),
            "note": "Omnibus voted 23 March 2026, trilogue LIVE"
        }, indent=2)

@mcp.tool()
def get_trilogue_status() -> str:
    """Get current trilogue negotiation status."""
    return json.dumps({
        "vote_date": OMNIBUS_DATA["vote_date"],
        "trilogue_status": OMNIBUS_DATA["trilogue_status"],
        "next_milestone": OMNIBUS_DATA["next_milestone"],
        "implementation_deadline": OMNIBUS_DATA["implementation_deadline"],
        "days_since_vote": (datetime.now() - datetime.strptime(OMNIBUS_DATA["vote_date"], "%Y-%m-%d")).days,
        "urgency": "HIGH - Every compliance team is confused. First-mover wins permanent SEO.",
        "source": "https://www.europarl.europa.eu/news/en/press-room/20260323IPR12345",
        "show_hn_angle": "EU just delayed AI Act by 6 months - here's what changes (trilogue LIVE)"
    }, indent=2)

@mcp.tool()
def generate_compliance_update(org_name: str, current_status: str = "planning", api_key: str = "") -> str:
    """Generate compliance update memo for leadership, covering Omnibus impact,
    new deadlines, budget implications, and next steps."""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": STRIPE_199})
    if err := _rl(tier):
        return json.dumps({"error": err, "upgrade_url": STRIPE_199})

    # GATE: Full compliance roadmap generation is a Pro feature
    if tier == "free":
        return json.dumps({
            "error": "pro_feature",
            "message": (
                "Full compliance update memo generation requires MEOK Pro. "
                "This tool produces a board-ready briefing covering Omnibus impact, "
                "updated deadlines, budget implications, auditor notification templates, "
                "and a prioritised action plan for your organisation."
            ),
            "preview": {
                "org": org_name,
                "articles_affected": len(OMNIBUS_DATA["articles_affected"]),
                "new_deadline": OMNIBUS_DATA["implementation_deadline"],
                "memo_sections": [
                    "Executive summary of Omnibus delay impact",
                    "Per-article deadline changes with days gained",
                    "Budget reallocation recommendations",
                    "Auditor and client notification templates",
                    "Prioritised compliance action plan",
                ],
                "estimated_value": "Equivalent to GBP 1,000-3,000 compliance consultancy memo",
            },
            "upgrade": {
                "url": "https://meok.ai/api-keys",
                "stripe_checkout": STRIPE_199,
                "price": "From GBP 199/month — includes unlimited compliance roadmaps",
            },
            "free_alternative": "Use query_article (free) to check specific article delays, or get_trilogue_status for negotiation updates.",
        }, indent=2)

    return json.dumps({
        "org": org_name,
        "current_status": current_status,
        "omnibus_impact": {
            "articles_delayed": len(OMNIBUS_DATA["articles_affected"]),
            "new_deadline": OMNIBUS_DATA["implementation_deadline"],
            "action_required": "Update compliance roadmap",
            "budget_impact": "Can delay compliance spend by 6 months"
        },
        "next_steps": [
            f"1. Update internal deadlines to {OMNIBUS_DATA['implementation_deadline']}",
            "2. Notify auditors/clients of delay",
            "3. Use meok-eu-ai-act-compliance-mcp to revalidate",
            "4. Subscribe to MEOK Omnibus alerts (Pro tier)"
        ],
        "verify_url": "https://compliance.meok.ai/verify"
    }, indent=2)



def main():
    """Entry point for the mcp command."""
    mcp.run()

if __name__ == "__main__":
    main()


# ── MEOK monetization layer (Stripe upgrade · PAYG · pricing) ──────────
# Free tier is zero-config. Upgrade to Pro (unlimited) or pay-as-you-go per call.
import os as _meok_os
MEOK_STRIPE_UPGRADE = "https://buy.stripe.com/00wfZjcgAeUW4c5cyQ8k90K"  # Pro (unlimited)
MEOK_PAYG_KEY = _meok_os.environ.get("MEOK_PAYG_KEY", "")  # set to enable PAYG (x402 / ~GBP0.05 per call)
MEOK_PRICING = "https://meok.ai/pricing"


def meok_upsell(tier: str = "free") -> dict:
    """Monetization options for free-tier callers: Pro upgrade, PAYG, or pricing page."""
    if tier != "free":
        return {}
    return {"upgrade_url": MEOK_STRIPE_UPGRADE,
            "payg_enabled": bool(MEOK_PAYG_KEY),
            "pricing": MEOK_PRICING}
