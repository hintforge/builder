# Claims that must all pass
**status:** research-integrated

Middle-dot separators.
_source: https://example.org/a · capture: web_fetch · confidence: high · enemy-tier: 0 · puzzle-tier: 0 · category: mainline_

Pipe separators.
_source: https://example.org/a · capture: web_fetch · confidence: high · enemy-tier: 1 | puzzle-tier: 0 | category: mainline_

Spaced-hyphen separators.
_source: https://example.org/a - capture: web_fetch - confidence: high - enemy-tier: 0 - puzzle-tier: 2 - category: mainline_

Wrapped over two lines.
_source: https://example.org/a · capture: web_fetch · confidence: high ·
enemy-tier: 0 · puzzle-tier: 0 · category: mainline_

Trailing text after the closing underscore.
_source: https://example.org/a · enemy-tier: 0 · puzzle-tier: 0_ — covers the paragraph above.

### Block claim
- **claim:** the door opens with the red key
- **source:** https://example.org/a
- **enemy-tier:** 0 | **puzzle-tier:** 1

### Fenced example (not content, must not be counted)
```
_source: · enemy-tier: 0_
- **claim:** an example
- **source:**
```
