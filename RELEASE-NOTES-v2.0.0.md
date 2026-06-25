# Compliance Atlas v2.0.0 — "The Briefings"

> The first public release shipped a dashboard. v2.0 ships a **briefing**.

## 🌊 What's new

- **Daily audio briefing** at the top of the dashboard — 30s TTS rundown of today's top regulatory signals
- **Per-jurisdiction deep dives** — 5 audio briefs (US Federal, EU, UK, Singapore, Japan) with custom SVG cover art
- **New 1200×630 OG image** with v2.0 branding + jurisdiction network map
- **Updated Reel kit** (`public/REEL.md`) with v2.0 launch narrative + 6 ready-to-ship TTS scripts

## ⚙️ What stayed the same

- False-failure reveal: 5,490 → 190, 28 → 5, 24/7 → real-time
- Live dashboard with KPIs, top critical findings, cross-jurisdiction conflicts
- All API endpoints (CORS-open, no auth, no rate limit)
- Data shape + filters

## 📦 Files changed

- `public/index.html` — +252 lines: briefing + jurisdiction sections + audio player JS
- `public/og.png` — Regenerated as v2.0
- `public/REEL.md` — v2.0 launch narrative + 6 TTS scripts
- `public/audio/` — New directory, 6 .mp3 files
- `curate.py` — Version bumped to 2.0.0
- `RELEASE-NOTES-v2.0.0.md` — Full release notes

## 🚀 Try it

```bash
git clone https://github.com/nvmmonsalud/compliance-atlas
cd compliance-atlas
git checkout v2.0.0
pip install -r requirements.txt
python curate.py
gunicorn api_combined:app --bind 0.0.0.0:8080
# Open http://localhost:8080
# Press play on the daily briefing
# Click any jurisdiction card for a region-specific brief
```

## 🛠️ Built with

This release was shipped using the full Hermes agent stack — TTS, vision, browser, delegate_task, gstack, PIL. The image_gen tool was unavailable in this environment, so I pivoted to SVG cover art (turned out cleaner & more brand-consistent anyway). Audio is edge-tts, free with no auth.

🌊 Built by NVM · Powered by a RegSwarm agent pipeline · Updated daily at 06:00 UTC
