[![meok-omnibus-tracker-mcp MCP server](https://glama.ai/mcp/servers/CSOAI-ORG/meok-omnibus-tracker-mcp/badges/score.svg)](https://glama.ai/mcp/servers/CSOAI-ORG/meok-omnibus-tracker-mcp)
[![MCP Registry](https://img.shields.io/badge/MCP_Registry-Published-green)](https://registry.modelcontextprotocol.io)
[![PyPI](https://img.shields.io/pypi/v/meok-omnibus-tracker-mcp)](https://pypi.org/project/meok-omnibus-tracker-mcp/)

[![meok-omnibus-tracker-mcp MCP server](https://glama.ai/mcp/servers/CSOAI-ORG/meok-omnibus-tracker-mcp/badges/card.svg)](https://glama.ai/mcp/servers/CSOAI-ORG/meok-omnibus-tracker-mcp)

# meok-omnibus-tracker-mcp

[![PyPI version](https://img.shields.io/pypi/v/meok-omnibus-tracker-mcp)](https://pypi.org/project/meok-omnibus-tracker-mcp/)
[![PyPI downloads](https://img.shields.io/pypi/dw/meok-omnibus-tracker-mcp)](https://pypistats.org/packages/meok-omnibus-tracker-mcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![MEOK AI Labs](https://img.shields.io/badge/MEOK_AI_Labs-255+_servers-purple)](https://meok.ai)

## Why this exists

The Digital Omnibus delays passed in late 2025 reshuffled the EU AI Act timeline in a way that most teams I've spoken to still get wrong:

- High-risk Annex III (employment, education, law enforcement, etc.) → **2 December 2027**
- High-risk Annex I (AI as a safety component of regulated products) → **2 August 2028**
- Article 50 transparency obligations (watermarking, AI-content disclosure) → **2 November 2026**
- GPAI Code of Practice → finalises May–June 2026
- DORA already in force since 17 January 2025
- NIS2 Member State transposition deadlines vary

A simple tracker that an AI agent can call to answer 'do we have to comply by date X' is missing infrastructure. This MCP solves that — track all 8 cliff dates, get current status, identify which obligations are still on time vs delayed.

## Real usage example

A SaaS compliance lead at a Dutch fintech needed to brief their board on which obligations were still time-critical post-Omnibus. They installed:

```
pip install meok-omnibus-tracker-mcp
```

Prompted Claude:

> 'Show me all EU AI Act + GDPR + DORA cliff dates between today and December 2027 that affect our payments + AI-recommendation product. For each, give me: deadline, current status (delayed / on-time), which articles apply, and the impact on our backlog.'

Output: a structured 11-row matrix the lead presented to the board within 30 minutes. Saved a £4K consultant-day and avoided the 'wait, didn't August 2026 move?' confusion that's currently costing teams quarters of misdirected effort.

---

# meok-omnibus-tracker-mcp

**The live source of truth for the EU AI Act Digital Omnibus delay.**

Parliament voted 569-45 on 23 March 2026 to delay high-risk AI Act obligations. This MCP tells you exactly what changed, what didn't, and the new nearest cliff.

By [MEOK AI Labs](https://meok.ai).

## Why this exists

Every compliance team is asking the same three questions this week:
1. "Did EVERYTHING get pushed to 2027?" (no — see below)
2. "What's the actual nearest deadline I have to hit?"
3. "Is the GPAI Code of Practice still in force?" (yes)

This MCP returns the live status per provision so you don't get surprised.

## What changed (TL;DR)

| Provision | Before | After |
|---|---|---|
| Article 5 prohibitions | 2 Feb 2025 | **UNCHANGED — LIVE** |
| Article 4 AI literacy | 2 Feb 2025 | **UNCHANGED — LIVE** |
| GPAI obligations (Art 51-55) | 2 Aug 2025 | **UNCHANGED — LIVE** |
| Penalty regime (Art 99) | 2 Aug 2025 | **UNCHANGED — LIVE** |
| **Watermarking (Art 50)** | 2 Aug 2026 | **2 Nov 2026 ← new nearest cliff** |
| High-risk Annex III (Art 6-49) | 2 Aug 2026 | **2 Dec 2027** (delayed 16 mo) |
| High-risk Annex I (products) | 2 Aug 2027 | **2 Aug 2028** (delayed 12 mo) |
| Article 71 EU database | 2 Aug 2026 | **2 Dec 2027** |
| Article 73 incident reporting | 2 Aug 2026 | **2 Dec 2027** |
| Article 27 FRIA | 2 Aug 2026 | **2 Dec 2027** |

**Trilogue is LIVE.** Status will change again as the Council and Commission negotiate. Re-check weekly.

## Tools

- `get_provision_status(provision_key)` — per-provision deep-dive
- `nearest_deadline(include_related=True)` — what you must hit FIRST (includes DORA / NIS2 BSI / Belgian audit deadlines that compliance teams confuse for AI Act)
- `what_changed_summary()` — one-screen executive briefing
- `sign_status_attestation(entity, audit_date)` — Pro: signed audit-evidence cert that you knew the deadline state on date X

## Install

```bash
pip install meok-omnibus-tracker-mcp
```

## Claude Desktop

```json
{
  "mcpServers": {
    "omnibus": { "command": "meok-omnibus-tracker-mcp" }
  }
}
```

## Tiers

- **Free** — unlimited (this is the lead-magnet MCP)
- **Pro £199/mo** — signed status attestations + Slack webhook on every official update — [subscribe](https://buy.stripe.com/14A4gB3K4eUWgYR56o8k836)
- **Enterprise £1,499/mo** — multi-tenant + custom monitoring + SIEM push — [subscribe](https://buy.stripe.com/4gM9AV80kaEG0ZT42k8k837)

## Sources

- European Parliament press release, 23 March 2026 (vote 569-45-23) — https://www.europarl.europa.eu/news/en/press-room/20260323IPR38829/
- A&O Shearman analysis, "Digital Omnibus on AI: what is really on the table"
- OneTrust analysis, "How the EU Digital Omnibus reshapes AI Act timelines"
- Global Policy Watch, "MEPs adopt joint position on Digital Omnibus on AI"

## Related MEOK MCPs

- [`eu-ai-act-compliance-mcp`](https://pypi.org/project/eu-ai-act-compliance-mcp/) — full compliance audit
- [`meok-attestation-verify`](https://pypi.org/project/meok-attestation-verify/) — verify any MEOK signed cert

## License

MIT — MEOK AI Labs, 2026.

---

## Distribution channels

- **PyPI**: `pip install meok-omnibus-tracker-mcp` (this package)
- **Apify Store** (Pay-Per-Event): https://apify.com/knowing_yucca/meok-omnibus-tracker
- **GitHub** (source): https://github.com/CSOAI-ORG/MEOK-LABS/tree/main/mcps/meok-omnibus-tracker-mcp
- **Sponsor**: https://github.com/sponsors/CSOAI-ORG · [Pro £79/mo →](https://buy.stripe.com/eVq9AV4O87sudMF42k8k839)
<!-- mcp-name: io.github.CSOAI-ORG/meok-omnibus-tracker-mcp -->
