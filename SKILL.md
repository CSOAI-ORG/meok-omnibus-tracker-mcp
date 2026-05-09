# meok-omnibus-tracker-mcp

## Description
EU Digital Omnibus AI Act tracker. Query delay status by article, track trilogue negotiations in real-time. Built after Parliament voted 23 March 2026.

## Category
compliance

## Use Cases
- Track EU AI Act Omnibus delay status
- Query specific article implementation deadlines
- Generate compliance update memos for leadership
- First-mover SEO advantage (trilogue LIVE)

## Installation
```bash
pip install meok-omnibus-tracker-mcp
```

## Quick Start
```python
from mcp import Client

client = Client("meok-omnibus-tracker-mcp")
result = client.call_tool("query_article", {"article": "11"})
print(result)
```

## Tools
- `query_article` - Check status of specific AI Act article
- `get_trilogue_status` - Live negotiation updates
- `generate_compliance_update` - Leadership memos

## Revenue Opportunity
- **Show HN angle:** "EU just delayed AI Act by 6 months — here's what changes"
- **Lead capture:** £199/mo Pro tier for automated alerts
- **First-mover:** Parliament voted 23 March 2026, trilogue ongoing

## Links
- MCP Server: https://github.com/CSOAI-ORG/meok-omnibus-tracker-mcp
- Documentation: https://meok.ai/docs/omnibus-tracker
- Live status: https://compliance.meok.ai/omnibus
