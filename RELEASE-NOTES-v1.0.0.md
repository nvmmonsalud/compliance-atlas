# v1.0.0 — Initial public release

## 🌊 5,490 findings. 28 jurisdictions. One screen.

The first public release of **Compliance Atlas** — a polished showcase of the RegSwarm regulatory monitoring pipeline.

## What's shipped

- **Curator** (`curate.py`): filters 5,490 raw findings → 190 curated public findings across 5 jurisdictions (US Federal, EU, UK, Singapore, Japan) and 2 sectors (fintech, crypto)
- **Combined API** (`api_combined.py`): single Flask app serving static `public/` + JSON API at `/api/*`
- **Landing page** (`public/index.html`): vanilla HTML/CSS/JS, dark theme, no build step, no external dependencies
- **Live data**: KPI cards + top critical findings + cross-jurisdiction conflicts fetched from same-origin API, refreshed every 60s
- **False-failure reveal**: animated count-up shows 5,490 → 190, 28 → 5, 24/7 → 61 critical
- **OG image** (1200×630) + **Reel kit** (60s + 90s scripts, 4-platform caption pack, TTS voice memo)
- **Render-ready**: `render.yaml` + `Procfile` for one-click deploy
- **Sample feed** bundled so the demo works without the private internal feed

## Try it

```bash
git clone https://github.com/nvmmonsalud/compliance-atlas
cd compliance-atlas
pip install -r requirements.txt
python curate.py
gunicorn api_combined:app --bind 0.0.0.0:8080
# Open http://localhost:8080
```

## API

| Endpoint | Returns |
|---|---|
| `GET /api/summary` | Aggregate stats |
| `GET /api/findings` | All findings (with `?severity`, `?jurisdiction`, `?sector`, `?limit` filters) |
| `GET /api/conflicts` | Cross-jurisdiction conflict cards |
| `GET /api/arbitrage` | Operational arbitrage opportunities |
| `GET /api/sectors` | Sector breakdown |
| `GET /api/health` | Liveness check |

All endpoints CORS-open. No auth. No rate limit. By design.

## The story

> "You can't track global regulation without a team of fifty."

This dashboard tracks **5,490 raw findings across 28 jurisdictions**, every day, with **one operator and one agent swarm**.

| What they say | What we do |
|---|---|
| Need a team of 50 | One operator + one agent swarm |
| Need enterprise SaaS | RSS feeds + LLM dedup |
| Need six-figure budget | Free tier on Render |
| Need a hundred dashboards | One screen, 5 jurisdictions |

## License

MIT — fork it, point it at your sector, run it on a Raspberry Pi if you want.

## Credits

- Built by [@nvmmonsalud](https://github.com/nvmmonsalud)
- Powered by a RegSwarm agent pipeline (5 LLM agents, RSS aggregation, daily regen)
- The internal atlas tracks 28 jurisdictions; this public version curates to 5
