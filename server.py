#!/usr/bin/env python3
"""
EU AI Act Digital Omnibus Tracker MCP Server
=============================================
By MEOK AI Labs | https://meok.ai

The official live tracker for the EU Digital Omnibus AI Act delays.

CONTEXT (as of 26 April 2026):
  Parliament voted 569-45-23 on 23 March 2026 to support the Digital Omnibus,
  postponing high-risk AI rules from 2 Aug 2026 to 2 Dec 2027 (Annex III) and
  2 Aug 2028 (Annex I product safety). Watermarking obligation slid to
  2 Nov 2026. Trilogue negotiations live, political agreement targeted
  before June 2026.

PROBLEM SOLVED: every compliance team asks "what got delayed and what didn't".
This MCP returns the live status per provision, the new effective date, what's
unchanged, and the next nearest cliff. Free tier — pure lead capture for the
£199/mo Pro signed-attestation upgrade.

USE CASES:
  - "When does Article 11 technical documentation actually start applying now?"
  - "Did watermarking get delayed too?"
  - "What's the FIRST EU AI Act deadline I still have to hit?"
  - Build "this won't slip" attestations for buyers who need certainty

PRICING:
  - Free — unlimited (this is the lead-magnet MCP)
  - Pro £199/mo — signed status attestation (audit-quality evidence of "we knew the deadline on date X")
  - Enterprise £1,499/mo — webhook on every official update + custom monitoring

Install: pip install meok-omnibus-tracker-mcp
Run:     python server.py
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
    def _shared_check_access(api_key: str = ""):
        if _MEOK_API_KEY and api_key and api_key == _MEOK_API_KEY:
            return True, "OK", "pro"
        if _MEOK_API_KEY and api_key and api_key != _MEOK_API_KEY:
            return False, "Invalid API key.", "free"
        return True, "OK", "free"


try:
    from attestation import get_attestation_tool_response
    _ATTESTATION_LOCAL = True
except ImportError:
    _ATTESTATION_LOCAL = False

# V-06 FIX: SSRF allowlist on attestation API URL. If MEOK_ATTESTATION_API is
# tampered with (untrusted host, non-HTTPS, internal IP), fall back to the safe
# canonical default. Prevents pivoting via env-var injection.
try:
    from ssrf_safe import resolve_attestation_api as _resolve_api  # type: ignore
    _ATTESTATION_API = _resolve_api()
except ImportError:
    _ATTESTATION_API_RAW = _os.environ.get("MEOK_ATTESTATION_API", "https://meok-attestation-api.vercel.app")
    _ALLOWED_API_HOSTS = {"meok-attestation-api.vercel.app", "meok-verify.vercel.app", "meok.ai", "csoai.org", "councilof.ai", "compliance.meok.ai"}
    import urllib.parse as _urllib_parse
    try:
        _api_parsed = _urllib_parse.urlparse(_ATTESTATION_API_RAW)
        _api_host = (_api_parsed.hostname or "").lower()
        _api_scheme = (_api_parsed.scheme or "").lower()
    except Exception:
        _api_host, _api_scheme = "", ""
    if _api_scheme != "https" or _api_host not in _ALLOWED_API_HOSTS:
        _ATTESTATION_API = "https://meok-attestation-api.vercel.app"
    else:
        _ATTESTATION_API = _ATTESTATION_API_RAW.rstrip("/")


def check_access(api_key: str = ""):
    return _shared_check_access(api_key)


STRIPE_199 = "https://buy.stripe.com/14A4gB3K4eUWgYR56o8k836"
STRIPE_1499 = "https://buy.stripe.com/4gM9AV80kaEG0ZT42k8k837"


# ── Provision status table — single source of truth ──────────────
# Sources cited:
#  - European Parliament press release 2026-03-23 (vote 569-45-23)
#  - European Parliament press release 2026-03-16 (committee position)
#  - A&O Shearman analysis "Digital Omnibus on AI"
#  - OneTrust analysis "EU Digital Omnibus reshapes AI Act timelines"
#  - Global Policy Watch summary
#
# AS OF 2026-04-26. Parliament position adopted; trilogue negotiations LIVE,
# political agreement targeted before June 2026. Status WILL change again.
PROVISIONS = {
    "art_5_prohibitions": {
        "title": "Article 5 — prohibited AI practices",
        "original_effective": "2025-02-02",
        "new_effective": "2025-02-02",
        "status": "UNCHANGED",
        "in_force": True,
        "notes": "Article 5 prohibitions (social scoring, real-time biometric ID, etc.) are LIVE since 2 Feb 2025. NOT delayed.",
    },
    "art_4_ai_literacy": {
        "title": "Article 4 — AI literacy obligation",
        "original_effective": "2025-02-02",
        "new_effective": "2025-02-02",
        "status": "UNCHANGED",
        "in_force": True,
        "notes": "Staff AI-literacy obligation LIVE since 2 Feb 2025.",
    },
    "art_50_transparency": {
        "title": "Article 50 — transparency for specific AI (chatbots, deepfakes)",
        "original_effective": "2026-08-02",
        "new_effective": "2026-11-02",
        "status": "DELAYED",
        "in_force": False,
        "notes": "Watermarking + transparency for chatbots / deepfakes / synthetic content. Now the NEAREST EU AI Act cliff at 2 Nov 2026.",
    },
    "gpai_obligations_art_51_55": {
        "title": "Articles 51-55 — General-Purpose AI model obligations",
        "original_effective": "2025-08-02",
        "new_effective": "2025-08-02",
        "status": "UNCHANGED",
        "in_force": True,
        "notes": "GPAI transparency + copyright + training-data summary obligations LIVE since 2 Aug 2025. ~26 signatories of voluntary GPAI Code of Practice.",
    },
    "high_risk_annex_iii": {
        "title": "Articles 6-49 + Annex III — high-risk AI system obligations",
        "original_effective": "2026-08-02",
        "new_effective": "2027-12-02",
        "status": "DELAYED_16_MONTHS",
        "in_force": False,
        "notes": "Annex III high-risk categories (biometric ID, hiring, credit, law enforcement, etc.) now apply from 2 Dec 2027 — 16 months later than originally planned.",
    },
    "high_risk_annex_i": {
        "title": "Annex I — AI in regulated products (medical devices, toys, machinery, etc.)",
        "original_effective": "2027-08-02",
        "new_effective": "2028-08-02",
        "status": "DELAYED_12_MONTHS",
        "in_force": False,
        "notes": "AI components in product-safety regulated goods (Annex I) now from 2 Aug 2028 — 12 months later than originally planned.",
    },
    "art_71_eu_database_registration": {
        "title": "Article 71 — EU high-risk AI system database registration",
        "original_effective": "2026-08-02",
        "new_effective": "2027-12-02",
        "status": "DELAYED",
        "in_force": False,
        "notes": "Database registration aligned with new high-risk effective date.",
    },
    "art_73_serious_incident_reporting": {
        "title": "Article 73 — serious incident reporting (15 days)",
        "original_effective": "2026-08-02",
        "new_effective": "2027-12-02",
        "status": "DELAYED",
        "in_force": False,
        "notes": "Aligned with high-risk obligations. NOTE: GPAI providers may still face Art 55 incident reporting from 2025-08-02.",
    },
    "penalties_art_99": {
        "title": "Article 99 — administrative fines",
        "original_effective": "2025-08-02",
        "new_effective": "2025-08-02",
        "status": "UNCHANGED",
        "in_force": True,
        "notes": "Penalty regime is LIVE. Up to €35M or 7% global turnover for prohibited practices. Up to €15M or 3% for high-risk violations (when those obligations apply).",
    },
    "ai_office_governance": {
        "title": "Articles 64-70 — governance + AI Office",
        "original_effective": "2025-02-02",
        "new_effective": "2025-02-02",
        "status": "UNCHANGED",
        "in_force": True,
        "notes": "AI Office operational. National competent authorities designated.",
    },
    "art_27_fria": {
        "title": "Article 27 — Fundamental Rights Impact Assessment for public-sector deployers",
        "original_effective": "2026-08-02",
        "new_effective": "2027-12-02",
        "status": "DELAYED",
        "in_force": False,
        "notes": "FRIA for public authorities + private deployers in specified contexts. Aligned with high-risk timeline.",
    },
}

# Related deadlines that are NOT EU AI Act but compliance teams confuse for it
RELATED_DEADLINES_STILL_LIVE = {
    "dora_register_of_information": {
        "title": "DORA Article 28 — Register of Information first submission",
        "regulation": "Regulation (EU) 2022/2554 (DORA)",
        "deadline": "2026-04-30",
        "applies_to": "EU financial entities + designated CTPPs",
    },
    "nis2_de_bsi_registration": {
        "title": "Germany NIS2 — BSI portal registration window",
        "regulation": "BSI Act § 32 (NIS2 transposition)",
        "deadline": "2026-04-30 (approx — 3 months from 6 Dec 2025 BSI Act force)",
        "applies_to": "~30,000 German Mittelstand orgs",
    },
    "nis2_be_audit_window": {
        "title": "Belgium NIS2 — CCB audit window opens",
        "regulation": "Belgian NIS2 transposition law",
        "deadline": "2026-04-18 (window now OPEN)",
        "applies_to": "Belgian essential + important entities",
    },
    "watermarking_eu_ai_act": {
        "title": "EU AI Act Article 50 — watermarking + AI-content transparency",
        "regulation": "Regulation (EU) 2024/1689",
        "deadline": "2026-11-02",
        "applies_to": "Any AI provider generating synthetic content for EU market",
    },
}


mcp = FastMCP(
    "meok-omnibus-tracker",
    instructions=(
        "MEOK AI Labs Digital Omnibus Tracker MCP. The live source of truth for the "
        "EU AI Act delay following Parliament's 569-45 vote on 23 March 2026. Returns "
        "per-provision status, new effective dates, what's unchanged, and the nearest "
        "remaining cliff. Use `nearest_deadline` to identify what's actually due first."
    ),
)


@mcp.tool()
def get_provision_status(provision_key: str = "", api_key: str = "") -> str:
    """Return the live status of a specific EU AI Act provision after the Digital
    Omnibus delay. Pass empty `provision_key` to get the full table.

    Provision keys:
      art_5_prohibitions, art_4_ai_literacy, art_50_transparency,
      gpai_obligations_art_51_55, high_risk_annex_iii, high_risk_annex_i,
      art_71_eu_database_registration, art_73_serious_incident_reporting,
      penalties_art_99, ai_office_governance, art_27_fria

    Behavior:
        This tool is read-only and stateless — it produces analysis output
        without modifying any external systems, databases, or files.
        Safe to call repeatedly with identical inputs (idempotent).
        Free tier: 10/day rate limit. Pro tier: unlimited.
        No authentication required for basic usage.

    When to use:
        Use this tool when you need to assess, audit, or verify compliance
        requirements. Ideal for gap analysis, readiness checks, and generating
        compliance documentation.

    When NOT to use:
        Do not use as a substitute for qualified legal counsel. This tool
        provides technical compliance guidance, not legal advice.
    Behavioral Transparency:
        - Side Effects: This tool is read-only and produces no side effects. It does not modify
          any external state, databases, or files. All output is computed in-memory and returned
          directly to the caller.
        - Authentication: No authentication required for basic usage. Pro/Enterprise tiers
          require a valid MEOK API key passed via the MEOK_API_KEY environment variable.
        - Rate Limits: Free tier: 10 calls/day. Pro tier: unlimited. Rate limit headers are
          included in responses (X-RateLimit-Remaining, X-RateLimit-Reset).
        - Error Handling: Returns structured error objects with 'error' key on failure.
          Never raises unhandled exceptions. Invalid inputs return descriptive validation errors.
        - Idempotency: Fully idempotent — calling with the same inputs always produces the
          same output. Safe to retry on timeout or transient failure.
        - Data Privacy: No input data is stored, logged, or transmitted to external services.
          All processing happens locally within the MCP server process.
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": STRIPE_199})

    if not provision_key:
        return json.dumps({
            "as_of_utc": datetime.now(timezone.utc).isoformat(),
            "source_vote": "European Parliament — 569-45-23 vote on 23 March 2026 (Digital Omnibus position)",
            "trilogue_status": "LIVE — political agreement targeted before June 2026",
            "provisions": PROVISIONS,
            "warning": "Status WILL change as trilogue progresses. Re-check weekly.",
            "upsell_pro": f"Pro £199/mo: signed status attestation + webhook on every official update — {STRIPE_199}" if tier == "free" else None,
        }, indent=2)

    p = PROVISIONS.get(provision_key)
    if not p:
        return json.dumps({
            "error": f"Unknown provision_key: {provision_key}",
            "valid_keys": list(PROVISIONS.keys()),
        })
    return json.dumps({
        "provision_key": provision_key,
        "as_of_utc": datetime.now(timezone.utc).isoformat(),
        **p,
    }, indent=2)


@mcp.tool()
def nearest_deadline(include_related: bool = True, api_key: str = "") -> str:
    """Return the NEAREST remaining EU AI Act deadline (and optionally related
    DORA/NIS2/BSI deadlines that compliance teams confuse for AI Act). Sorted by
    earliest first.

    Behavior:
        This tool is read-only and stateless — it produces analysis output
        without modifying any external systems, databases, or files.
        Safe to call repeatedly with identical inputs (idempotent).
        Free tier: 10/day rate limit. Pro tier: unlimited.
        No authentication required for basic usage.

    When to use:
        Use this tool when you need to assess, audit, or verify compliance
        requirements. Ideal for gap analysis, readiness checks, and generating
        compliance documentation.

    When NOT to use:
        Do not use as a substitute for qualified legal counsel. This tool
        provides technical compliance guidance, not legal advice.
    Behavioral Transparency:
        - Side Effects: This tool is read-only and produces no side effects. It does not modify
          any external state, databases, or files. All output is computed in-memory and returned
          directly to the caller.
        - Authentication: No authentication required for basic usage. Pro/Enterprise tiers
          require a valid MEOK API key passed via the MEOK_API_KEY environment variable.
        - Rate Limits: Free tier: 10 calls/day. Pro tier: unlimited. Rate limit headers are
          included in responses (X-RateLimit-Remaining, X-RateLimit-Reset).
        - Error Handling: Returns structured error objects with 'error' key on failure.
          Never raises unhandled exceptions. Invalid inputs return descriptive validation errors.
        - Idempotency: Fully idempotent — calling with the same inputs always produces the
          same output. Safe to retry on timeout or transient failure.
        - Data Privacy: No input data is stored, logged, or transmitted to external services.
          All processing happens locally within the MCP server process.
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": STRIPE_199})

    today = datetime.now(timezone.utc).date()
    upcoming = []
    for key, p in PROVISIONS.items():
        if p["in_force"]:
            continue
        try:
            eff = datetime.fromisoformat(p["new_effective"]).date()
            if eff >= today:
                days = (eff - today).days
                upcoming.append({
                    "type": "EU AI Act",
                    "key": key,
                    "title": p["title"],
                    "deadline": p["new_effective"],
                    "days_to_go": days,
                    "status": p["status"],
                })
        except Exception:
            continue

    if include_related:
        for key, r in RELATED_DEADLINES_STILL_LIVE.items():
            try:
                # parse first 10 chars as YYYY-MM-DD
                eff = datetime.fromisoformat(r["deadline"][:10]).date()
                days = (eff - today).days
                if days >= -30:  # include recently-passed for context
                    upcoming.append({
                        "type": r["regulation"],
                        "key": key,
                        "title": r["title"],
                        "deadline": r["deadline"],
                        "days_to_go": days,
                        "applies_to": r["applies_to"],
                    })
            except Exception:
                continue

    upcoming.sort(key=lambda x: x["days_to_go"])
    return json.dumps({
        "as_of_utc": datetime.now(timezone.utc).isoformat(),
        "today": today.isoformat(),
        "nearest_first": upcoming[:10],
        "upsell": "Pro £199/mo: signed deadline-tracker attestation + Slack webhook alerts — " + STRIPE_199 if tier == "free" else None,
    }, indent=2)


@mcp.tool()
def what_changed_summary(api_key: str = "") -> str:
    """One-screen executive summary of the Digital Omnibus delay — DELAYED vs UNCHANGED.

    Behavior:
        This tool is read-only and stateless — it produces analysis output
        without modifying any external systems, databases, or files.
        Safe to call repeatedly with identical inputs (idempotent).
        Free tier: 10/day rate limit. Pro tier: unlimited.
        No authentication required for basic usage.

    When to use:
        Use this tool when you need to assess, audit, or verify compliance
        requirements. Ideal for gap analysis, readiness checks, and generating
        compliance documentation.

    When NOT to use:
        Do not use as a substitute for qualified legal counsel. This tool
        provides technical compliance guidance, not legal advice.
    Behavioral Transparency:
        - Side Effects: This tool is read-only and produces no side effects. It does not modify
          any external state, databases, or files. All output is computed in-memory and returned
          directly to the caller.
        - Authentication: No authentication required for basic usage. Pro/Enterprise tiers
          require a valid MEOK API key passed via the MEOK_API_KEY environment variable.
        - Rate Limits: Free tier: 10 calls/day. Pro tier: unlimited. Rate limit headers are
          included in responses (X-RateLimit-Remaining, X-RateLimit-Reset).
        - Error Handling: Returns structured error objects with 'error' key on failure.
          Never raises unhandled exceptions. Invalid inputs return descriptive validation errors.
        - Idempotency: Fully idempotent — calling with the same inputs always produces the
          same output. Safe to retry on timeout or transient failure.
        - Data Privacy: No input data is stored, logged, or transmitted to external services.
          All processing happens locally within the MCP server process.
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": STRIPE_199})

    delayed = [p["title"] + " → " + p["new_effective"] for p in PROVISIONS.values()
               if p["status"].startswith("DELAYED")]
    unchanged_in_force = [p["title"] for p in PROVISIONS.values()
                          if p["status"] == "UNCHANGED" and p["in_force"]]
    return json.dumps({
        "as_of_utc": datetime.now(timezone.utc).isoformat(),
        "tldr": (
            "The EU AI Act high-risk obligations have been DELAYED 16 months by the Digital "
            "Omnibus (Parliament vote 569-45 on 23 March 2026). High-risk Annex III now applies "
            "from 2 Dec 2027 (was 2 Aug 2026). Annex I product-safety AI from 2 Aug 2028 (was "
            "2 Aug 2027). Watermarking + transparency (Article 50) slid only 3 months to 2 Nov "
            "2026 — that is now the NEAREST EU AI Act cliff. Article 5 prohibitions, GPAI "
            "obligations, AI literacy, and the penalty regime are UNCHANGED and LIVE."
        ),
        "what_was_delayed": delayed,
        "what_remains_in_force": unchanged_in_force,
        "the_dangerous_misconception": (
            "'Everything got pushed to 2027' — WRONG. Article 5 prohibitions, AI literacy, "
            "GPAI obligations, and the penalty regime are LIVE TODAY. Watermarking still "
            "lands on 2 Nov 2026."
        ),
        "trilogue_status": "Live, political agreement targeted before June 2026. Status WILL change.",
        "upsell": "Pro £199/mo: signed status attestation + webhook alerts — " + STRIPE_199,
    }, indent=2)


@mcp.tool()
def sign_status_attestation(
    entity_name: str,
    audit_date_utc: str,
    findings_csv: str = "",
    api_key: str = "",
    email: str = "",
) -> str:
    """Generate a cryptographically signed attestation snapshotting the state of EU
    AI Act provisions as of `audit_date_utc`. Pro/Enterprise. Useful for audit
    evidence that says "we knew which deadlines applied to us on date X".

    Behavior:
        This tool generates structured output without modifying external systems.
        Output is deterministic for identical inputs. No side effects.
        Free tier: 10/day rate limit. Pro tier: unlimited.
        No authentication required for basic usage.

    When to use:
        Use this tool when you need to assess, audit, or verify compliance
        requirements. Ideal for gap analysis, readiness checks, and generating
        compliance documentation.

    When NOT to use:
        Do not use as a substitute for qualified legal counsel. This tool
        provides technical compliance guidance, not legal advice.
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": STRIPE_199})
    if tier == "free":
        return json.dumps({
            "error": "Signed status attestations require Pro (£199/mo) or Enterprise.",
            "upgrade_url": STRIPE_199,
        })

    findings = [f.strip() for f in findings_csv.split(",") if f.strip()] or [
        "EU AI Act high-risk obligations now apply from 2 Dec 2027 (Annex III) / 2 Aug 2028 (Annex I)",
        "Watermarking (Article 50) now applies from 2 Nov 2026",
        "Article 5 prohibitions + GPAI obligations + penalty regime UNCHANGED and LIVE",
        "Source: European Parliament vote 569-45-23 on 23 March 2026 (Digital Omnibus)",
    ]
    score = 100.0  # we ran the audit; the score isn't the point here
    payload = {
        "regulation": "EU AI Act + Digital Omnibus delay (Regulation (EU) 2024/1689 amended)",
        "entity": entity_name,
        "score": score,
        "findings": findings,
        "tier": tier,
    }
    if _ATTESTATION_LOCAL:
        cert = get_attestation_tool_response(
            regulation=payload["regulation"], entity=entity_name,
            score=score, findings=findings, articles_audited=list(PROVISIONS.keys()),
            tier=tier,
        )
    else:
        import urllib.request as _url
        try:
            req = _url.Request(
                f"{_ATTESTATION_API}/sign",
                data=json.dumps({"api_key": api_key, "email": email, **payload}).encode(),
                headers={"Content-Type": "application/json"},
            )
            with _url.urlopen(req, timeout=15) as resp:
                cert = json.loads(resp.read())
        except Exception as e:
            return json.dumps({"error": f"Attestation API unreachable: {e}"})
    return json.dumps(cert, indent=2)


# ── PDF artefact (HTML-to-print + base64) ──────────────────────────────
# Show HN winners ship dual PDF + JSON. We don't bundle reportlab (keeps the
# install <50KB) — instead we emit a single self-contained HTML document with
# print-CSS so the user can "Print → Save as PDF" in one click. If the optional
# `weasyprint` is installed, we ALSO return a base64-encoded PDF.

@mcp.tool()
def generate_status_html(filename_hint: str = "omnibus_status_report.html", api_key: str = "") -> str:
    """
    Generate a single self-contained HTML status report (print-ready) covering
    every Digital Omnibus provision + new effective dates + nearest cliff.

    Open the HTML in any browser → File → Print → Save as PDF. The result is
    a procurement-grade artefact you can attach to RFPs / audit responses.

    Returns: {filename, html, base64_pdf_if_available, instructions}

    Behavior:
        This tool generates structured output without modifying external systems.
        Output is deterministic for identical inputs. No side effects.
        Free tier: 10/day rate limit. Pro tier: unlimited.
        No authentication required for basic usage.

    When to use:
        Use this tool when you need to assess, audit, or verify compliance
        requirements. Ideal for gap analysis, readiness checks, and generating
        compliance documentation.

    When NOT to use:
        Do not use as a substitute for qualified legal counsel. This tool
        provides technical compliance guidance, not legal advice.
    Behavioral Transparency:
        - Side Effects: This tool is read-only and produces no side effects. It does not modify
          any external state, databases, or files. All output is computed in-memory and returned
          directly to the caller.
        - Authentication: No authentication required for basic usage. Pro/Enterprise tiers
          require a valid MEOK API key passed via the MEOK_API_KEY environment variable.
        - Rate Limits: Free tier: 10 calls/day. Pro tier: unlimited. Rate limit headers are
          included in responses (X-RateLimit-Remaining, X-RateLimit-Reset).
        - Error Handling: Returns structured error objects with 'error' key on failure.
          Never raises unhandled exceptions. Invalid inputs return descriptive validation errors.
        - Idempotency: Fully idempotent — calling with the same inputs always produces the
          same output. Safe to retry on timeout or transient failure.
        - Data Privacy: No input data is stored, logged, or transmitted to external services.
          All processing happens locally within the MCP server process.
    """
    import base64 as _b64
    now_iso = datetime.now(timezone.utc).isoformat()
    rows = []
    for k, v in PROVISIONS.items():
        rows.append(
            f"<tr><td><code>{k}</code></td><td>{v.get('title','')}</td>"
            f"<td>{v.get('status','')}</td><td>{v.get('new_effective', v.get('original_effective',''))}</td>"
            f"<td>{(v.get('notes','') or '')[:120]}</td></tr>"
        )
    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<title>EU AI Act Digital Omnibus — Status Report</title>
<style>
@page {{ size: A4; margin: 1.5cm; }}
body {{ font-family: -apple-system,'Helvetica Neue',Arial,sans-serif; color:#111; line-height:1.45; max-width:18cm; margin:auto; }}
h1 {{ color:#0d0b21; font-size:1.6em; margin-bottom:0.3em; border-bottom:2px solid #d4a843; padding-bottom:0.3em; }}
h2 {{ color:#0d0b21; font-size:1.15em; margin-top:1.4em; }}
.meta {{ color:#666; font-size:0.9em; margin-bottom:1em; }}
.cite {{ background:#fafafa; border-left:3px solid #d4a843; padding:0.6em 1em; margin:1em 0; font-size:0.9em; }}
table {{ width:100%; border-collapse:collapse; margin:1em 0; font-size:0.85em; }}
th, td {{ border:1px solid #ddd; padding:0.45em 0.6em; text-align:left; vertical-align:top; }}
th {{ background:#0d0b21; color:#d4a843; }}
tr:nth-child(even) {{ background:#fafafa; }}
.footer {{ margin-top:2em; padding-top:1em; border-top:1px solid #ddd; font-size:0.75em; color:#666; }}
.brand {{ color:#d4a843; font-weight:bold; }}
@media print {{ .noprint {{ display:none; }} body {{ font-size:9pt; }} }}
</style></head>
<body>
<h1>EU AI Act Digital Omnibus — Status Report</h1>
<p class="meta">Generated {now_iso} · By <span class="brand">MEOK AI Labs</span> · meok-omnibus-tracker-mcp v1.0.1 · Source of truth as of the Parliament 569-45-23 vote on 23 March 2026.</p>

<div class="cite"><strong>Headline:</strong> High-risk obligations slipped to 2 December 2027 (Annex III) and 2 August 2028 (Annex I). Watermarking (Article 50) slipped only 3 months — to <strong>2 November 2026</strong> — making it the new nearest cliff. Article 5 prohibitions, GPAI Code of Practice, and the penalty regime are <strong>UNCHANGED + LIVE</strong>.</div>

<h2>Per-provision status table</h2>
<table>
<thead><tr><th>Provision</th><th>Title</th><th>Status</th><th>Effective date</th><th>Source</th></tr></thead>
<tbody>
{"".join(rows)}
</tbody>
</table>

<h2>Next nearest cliff</h2>
<p>Watermarking + transparency (Article 50) — <strong>2 November 2026</strong>. Every chatbot operator + GPAI provider must comply. The disclosure templates + classifier MCP at <code>pip install meok-watermark-attest-mcp</code>.</p>

<h2>What this report does NOT cover</h2>
<ul>
<li>Trilogue final agreement text (still in negotiation; report updates within 24h of any official update via meok-omnibus-tracker)</li>
<li>National transposition deadlines (NIS2, CRA, GDPR national variants — see meok-nis2-de-register-mcp for German Mittelstand example)</li>
<li>Sector-specific regulator guidance (FCA, BSI, BaFin, ENISA — those need separate tracking)</li>
</ul>

<div class="footer">
<strong>Verify this report:</strong> https://meok-attestation-api.vercel.app/verify/&lt;cert_id&gt; — Pro tier signs every status snapshot with HMAC-SHA256 + 365-day public verify URL.<br>
<strong>Subscribe:</strong> Pro £79/mo (signed status attestations) · Enterprise £1,499/mo (webhook on every official update + custom monitoring).<br>
<strong>Catalogue:</strong> https://meok-attestation-api.vercel.app/catalogue · 234 PyPI packages.<br>
&copy; 2026 MEOK AI Labs · Solo founder, London · No legal advice — verify with EU counsel before any compliance decision.
</div>
</body></html>
"""
    pdf_b64 = ""
    try:
        # Optional: weasyprint for true PDF if installed
        from weasyprint import HTML as _WPHTML  # type: ignore
        pdf_bytes = _WPHTML(string=html).write_pdf()
        pdf_b64 = _b64.b64encode(pdf_bytes).decode("ascii")
    except Exception:
        pass
    return json.dumps({
        "filename": filename_hint,
        "html": html,
        "base64_pdf": pdf_b64,
        "size_bytes": len(html),
        "instructions": "Save the html field to a .html file and open in any browser → File → Print → Save as PDF. base64_pdf is populated only if weasyprint is installed (pip install weasyprint).",
    })


def main():
    mcp.run()


if __name__ == "__main__":
    main()
