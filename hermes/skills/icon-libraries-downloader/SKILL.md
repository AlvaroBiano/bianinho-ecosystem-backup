---
name: icon-libraries-downloader
description: Download and organize free SVG icon libraries from GitHub into a unified local collection.
category: productivity
status: completed
completed: "2026-04-24"
---

# Icon Libraries Downloader

Download and organize free SVG icon libraries from GitHub into a unified local collection.

## STATUS: ALREADY EXECUTED (24/04/2026)

All 17 collections are already downloaded and organized at:
- `~/icon-libraries/organized/` — 35,991 icons across 17 collections (161 MB)
- `~/fontawesome-free/` — Font Awesome Free v7.2.0 (2,860 icons, 41 MB)

**GitHub repo:** github.com/AlvaroBiano/icon-assets
**Cross-library lookup:** `~/icon-libraries/organized/cross-library-lookup.json`
**Quick search script:** `python3 ~/.hermes/scripts/icon-lookup.py <icon-name>`

## When to Use

Use when asked to download icon sets, build an icon library, or gather SVGs from GitHub repositories.

## What It Does

Downloads multiple free icon libraries from GitHub, extracts individual SVG files, and organizes them by collection with cross-library search indices.

## Known Icon Libraries (verified free licenses)

| Library | GitHub Repo | SVG Source Path | Pattern | Notes |
|---------|-----------|-----------------|---------|-------|
| feather | feathericons/feather | feather/icons | *.svg | 287 icons |
| heroicons | tailwindlabs/heroicons | heroicons/optimized | **/*.svg | 1288 icons, 3 sizes |
| simple-icons | simple-icons/simple-icons | simple-icons/icons | *.svg | Brand logos, 3429 |
| lucide | lucide-icons/lucide | lucide/icons | *.svg | 1699 icons |
| tabler-icons | tabler/tabler-icons | tabler-icons/icons | outline/*.svg, filled/*.svg | 5039+1053 |
| devicon | devicons/devicon | devicon/icons | **/*.svg | Subdirs per icon |
| css-gg | astrit/css.gg | css.gg/icons/svg | *.svg | 704 icons |
| open-iconic | iconic/open-iconic | open-iconic/svg | *.svg | 223 icons |
| remixicon | Remix-Design/RemixIcon | RemixIcon/icons | **/*.svg | 3229 icons |
| octicons | primer/octicons | octicons/icons | *.svg | 729 icons |
| eva-icons | akveo/eva-icons | eva-icons | **/*.svg | 495 icons |
| iconpark | bytedance/IconPark | IconPark | **/*.svg | 2658 icons |
| iconoir | iconoir-icons/iconoir | iconoir/icons | regular/*.svg, solid/*.svg | 1383+288 |
| bootstrap-icons | twbs/icons | icons/icons | *.svg | 2078 icons |
| mingcute | mingcute-design/mingcute-icons | mingcute-icons | **/*.svg | 3325 icons |
| phosphor | phosphor-icons/phosphor-home | phosphor-home/public/assets/phosphor.iconjar/icons | *.svg | 9072 total, 1512 unique (dedup by weight) |
| thesvg | glincker/thesvg | thesvg/public/icons | * (folders) | Pick default.svg from each folder |

## Extraction Strategy

### Standard libraries
```python
shutil.copytree(src_dir, dest_dir)
```

### Phosphor (deduplicate weights)
Each icon has 6 weights: thin, light, regular, bold, fill, duotone.
Pick ONE per icon (prefer regular, then fill, then first found).
```python
# Group by icon name (strip weight suffix)
seen = {}
for svg in sorted(phosphor_src.glob("*.svg")):
    name = svg.stem
    for suffix in ['-thin', '-light', '-fill', '-bold', '-duotone']:
        if name.endswith(suffix):
            icon_name = name[:-len(suffix)]
            break
    if icon_name not in seen:
        seen[icon_name] = svg
```

### TheSvg (one variant per icon)
Each icon has a folder with multiple variants (default, mono, light, dark, color, wordmark...).
Pick default.svg from each folder.
```python
for folder in icon_folders:
    default = folder / "default.svg"
    if default.exists():
        shutil.copy2(default, dest / f"{folder.name}.svg")
```

## Organization Structure

```
~/icon-libraries/
├── organized/
│   ├── feather/
│   ├── heroicons/
│   ├── simple-icons/
│   ├── tabler-icons/
│   │   ├── outline/
│   │   └── filled/
│   ├── phosphor/
│   ├── thesvg/
│   └── ... (one folder per collection)
├── master-index.json
├── cross-library-lookup.json
└── README.md
```

## Important Gotchas

1. **Background git clone goes to CWD**: When running `git clone` in background with `&`, it clones to the current working directory of the shell, NOT the explicitly `cd`'d directory. Always verify after cloning.

2. **Phosphor-home ≠ Phosphor icons**: The phosphor-home repo is the website. The actual SVG icons are in `phosphor-home/public/assets/phosphor.iconjar/icons/`.

3. **Heroicons has 3 sizes**: 16/, 20/, 24/ subdirs. If copying only one, use 24/ or copy all with **/*.svg.

4. **Devicon has subfolders**: Each icon (aarch64, adonisjs, etc.) has 3 SVG variants inside the subfolder. Use **/*.svg to get all.

5. **RemixIcon folder name**: Clone creates "RemixIcon" (capital R+I), not "remixicon".

6. **FluentUI Emoji**: Has 7885 assets but they're emoji/illustrations, not UI icons. Skip for icon library use.

7. **Iconify**: Is a meta-aggregator (150 icon sets). The repo doesn't contain SVGs directly — skip.

## Create Cross-Library Lookup

After extracting, build a lookup for finding icons by name:
```python
lookup = {}
for coll_dir in organized_base.iterdir():
    for svg in coll_dir.glob("**/*.svg"):
        name = svg.stem.lower()
        lookup.setdefault(name, []).append(str(svg.relative_to(organized_base)))
with open(organized_base / "cross-library-lookup.json", "w") as f:
    json.dump(lookup, f, ensure_ascii=False, indent=2)
```

## License Notes

- MIT, Apache-2.0, CC0-1.0, ISC, OFL are all free for commercial use
- Always attribute as required by each license
- Font Awesome Free (OFL) is separate — download via NPM package, not scraping

## Verification Commands

```bash
# Count SVGs per collection
find ~/icon-libraries/organized -name "*.svg" | wc -l

# Check specific library
find ~/icon-libraries/organized/lucide -name "*.svg" | wc -l

# Find duplicates (icons in multiple libraries)
jq 'map_values(length) | to_entries[] | select(.value > 1)' cross-library-lookup.json
```
