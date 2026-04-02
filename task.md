# Task Checklist: AI Resume Analyzer

## Configuration
- `[x]` Vercel config (`vercel.json`)
- `[x]` Python requirements (`requirements.txt`)

## Backend
- `[x]` `api/index.py` — FastAPI main app with routes
- `[x]` `api/utils/parser.py` — PDF extraction
- `[x]` `api/utils/matcher.py` — TF-IDF + cosine similarity
- `[x]` `api/utils/skills.py` — Dynamic skill extraction
- `[x]` `api/utils/scoring.py` — Combined scoring engine (50/30/20)
- `[x]` `api/utils/ai_module.py` — AI suggestions + bullet rewriting (FIXED)

## Frontend
- `[x]` `public/index.html` — Full SPA layout
- `[x]` `public/styles/main.css` — Dark theme, glassmorphism, neon accents
- `[x]` `public/scripts/app.js` — Interactivity, API calls, animations

## Local Dev
- `[x]` `run_dev.py` — Local dev server serving both frontend + API

## Bug Fixes
- `[x]` Rewriter bug: was only adding bullets, now genuinely transforms content
- `[x]` Multi-line sentence merging
- `[x]` JD-aware keyword injection (selective, not spammy)

## Verification
- `[x]` Local test with sample PDF — analyze endpoint
- `[x]` Rewrite endpoint with JD context
- `[x]` Browser UI verification (screenshots captured)
