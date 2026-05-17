# music-graphs

A local Flask app for exploring curated music knowledge as interactive graphs. Each graph is a hand-authored set of cards (people, albums, tracks, places) connected by wikilinks, rendered with vis-network and playable via embedded Spotify players.

## Prerequisites

- Python 3.11+

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
python app.py
```

Then open <http://127.0.0.1:8766/> in your browser.

## Tests

```bash
pytest tests/ -v
```
