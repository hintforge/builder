# Claims that must each be flagged
**status:** reconciled

Empty source.
_source:  · capture: web_fetch · enemy-tier: 0 · puzzle-tier: 0_

Missing puzzle-tier.
_source: https://example.org/a · capture: web_fetch · enemy-tier: 0_

Missing both tiers.
_source: https://example.org/a · capture: web_fetch_

### Block with empty source
- **claim:** c
- **source:**
- **enemy-tier:** 0 | **puzzle-tier:** 0

### Block missing enemy-tier
- **claim:** d
- **source:** https://example.org/a
- **puzzle-tier:** 0
