# Icon Library — Local SVG Icon Collection

**ESTOU COM ACESSO a uma coleção local de ícones SVG. Posso usar ícones diretamente sem buscar online.**

Total: **35,991 SVGs** em 17 coleções GitHub + Font Awesome Free (2,860 ícones)

## Coleções Disponíveis

## Icon Collections

Primary path: `~/icon-libraries/organized/`

| Collection | Icons | Best For |
|-----------|-------|----------|
| tabler-icons | 6,092 | Detailed UI, outline + filled |
| thesvg | 5,661 | Brand logos, multi-variant |
| simple-icons | 3,429 | Brand logos, monochrome |
| mingcute | 3,325 | Clean line icons, rounded |
| remixicon | 3,229 | General purpose icons |
| iconpark | 2,658 | Line icons, ByteDance style |
| bootstrap-icons | 2,078 | Bootstrap ecosystem |
| devicon | 1,877 | Developer tools/tech logos |
| lucide | 1,699 | Clean minimal line icons |
| iconoir | 1,671 | Minimal line + solid |
| phosphor | 1,512 | Multi-weight icons |
| octicons | 729 | GitHub-style UI icons |
| css-gg | 704 | Uniform CSS-style icons |
| eva-icons | 493 | 48px grid icons |
| heroicons | 324 | Tailwind-style icons |
| feather | 287 | Ultra-minimal line icons |
| open-iconic | 223 | Open source icon set |

**Plus: Font Awesome Free v7.2.0** at `~/fontawesome-free/icons-by-category/`:
- solid: 2,000 | brands: 587 | regular: 273

## Index Files

- `~/icon-libraries/organized/cross-library-lookup.json` — Search icon name → library path
- `~/icon-libraries/organized/master-index.json` — Full collection summary
- `~/icon-libraries/organized/<collection>-index.json` — Per-collection name map
- `~/fontawesome-free/icons-by-category/icon-lookup.json` — Font Awesome lookup
- `~/fontawesome-free/icons-by-category/master-index.json` — Font Awesome summary

## Finding Icons

```bash
# Search for "heart" across all 17 collections
grep "heart" ~/icon-libraries/organized/cross-library-lookup.json

# List all icons in a collection
ls ~/icon-libraries/organized/lucide/ | head -20

# Find brand logos
ls ~/icon-libraries/organized/simple-icons/ | grep github

# Find specific icon in Font Awesome
grep "github" ~/fontawesome-free/icons-by-category/icon-lookup.json
```

## Using Icons in Code

```python
import json
from pathlib import Path

# Load cross-library lookup
lookup = json.loads(
    Path("~/icon-libraries/organized/cross-library-lookup.json").read_text()
)

# Find "heart" icon
heart_results = lookup.get("heart", [])
# Returns: ['tabler-icons/outline/heart.svg', 'lucide/heart.svg', ...]

# Load Font Awesome lookup
fa_lookup = json.loads(
    Path("~/fontawesome-free/icons-by-category/icon-lookup.json").read_text()
)
```

## Adding New Icons

1. Download from GitHub (verify license first)
2. Place SVG in appropriate collection under `~/icon-libraries/organized/<collection>/`
3. Update index: re-run the index generation script
4. Commit to GitHub if applicable

## Performance Notes

- All icons are individual `.svg` files — no bundling needed
- Total organized size: 161 MB
- Cross-library lookup loads into memory easily (~2MB JSON)
- For web interfaces, consider caching commonly used icons
