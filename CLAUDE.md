# yc-intelligence — YC Batch Intelligence 2025

> Sitio público con el estudio completo de 589 startups de Y Combinator 2025 + herramientas para preparar tu pitch.

## Stack
- Python, Flask
- HTML5 + Tailwind CSS (CDN) + vanilla JS
- Bilingual (EN/ES)

## URL
- yc-intelligence.pabesfu.com (Cloudflare tunnel, port 5054)

## Pages
- `/` — Landing page: batch data, alumni, numbers, partner quotes, podcast, reports
- `/builder` — YC Application Builder (AI-powered form)
- `/health` — Health check
- `/api/companies` — Search/filter 589 startups (params: q, batch, category, limit, offset)
- `/api/stats` — Aggregate statistics + intelligence data
- `/api/company/<name>` — Individual startup profile

## Data
- `data/yc_2025_master_list.json` — 589 startups, 24 fields each (1.09 MB)
- `data/yc_intelligence.txt` — Portfolio metrics, benchmarks, RFS 2026

## Key Numbers
- 589 total companies (W25: 203, S25: 214, F25: 172)
- 91.5% AI-native
- 22.2% AI Agents (131 startups)
- 63% teams have exactly 2 founders

## Project Structure
```
yc-intelligence/
├── app.py              # Flask app (routes + API)
├── requirements.txt    # flask, gunicorn
├── sections_new.py     # YC form sections config
├── templates/
│   ├── index.html      # Landing page (1669 lines, bilingual)
│   └── builder.html    # YC Application Builder
├── data/
│   ├── yc_2025_master_list.json  # 589 startups
│   └── yc_intelligence.txt       # Portfolio intel
├── static/             # CSS, PDFs, media
├── CLAUDE.md           # This file
└── .gitignore
```

## Separated from
- `pabesfu/autonomous-yc` — Internal Autonomous command center (private)
- `pabesfu/yc-2025-research` — Raw research data, podcasts, videos (private)

This project is PUBLIC — contains no internal Autonomous info.

## Services
- com.pabesfu.yc-intelligence.plist (port 5054, RunAtLoad)

## Commit Conventions
feat: / fix: / docs: / ops:

## Team
- Pablo (pabesfu) — Owner
