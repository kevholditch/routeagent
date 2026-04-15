# routeagent

An AI-powered circular running route planner. Give it a location and a target distance and it will plan a circular route, render an interactive map, and export a GPX file ready to load onto your watch.

## How it works

The tool uses Claude as an AI agent to:

1. Geocode your starting location into coordinates
2. Generate a circular route at your target distance using OpenRouteService
3. Check the actual distance and retry with different route variations if needed
4. Render an interactive HTML map and export a GPX file

## Prerequisites

- Python 3.10+
- An Anthropic API key
- An OpenRouteService API key

## API key setup

### Anthropic API key

1. Go to [console.anthropic.com](https://console.anthropic.com) and sign in or create an account
2. Navigate to **API Keys** and create a new key
3. Copy the key — it starts with `sk-ant-...`

### OpenRouteService API key

OpenRouteService provides the routing engine that generates the actual road/path geometry.

1. Go to [openrouteservice.org](https://openrouteservice.org) and create a free account
2. From your dashboard, go to **API Keys** and create a new token
3. The free tier allows 2,000 requests/day which is more than enough for personal use

### Configure your keys

Copy the example env file and fill in your keys:

```bash
cp .env.example .env
```

Edit `.env`:

```
ANTHROPIC_API_KEY=sk-ant-...
ORS_API_KEY=your-openrouteservice-key
```

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python cli.py --location "LOCATION" --distance DISTANCE_KM
```

### Examples

Plan a 10 km route from Cambourne, Cambridge:

```bash
python cli.py -l "Cambourne, Cambridge" -d 10
```

Plan a flat 5 km route:

```bash
python cli.py -l "Hyde Park, London" -d 5 --prefer "flat"
```

Plan 3 different route variants on the same map:

```bash
python cli.py -l "Edinburgh city centre" -d 8 --variants 3
```

Plan a route without opening the browser automatically:

```bash
python cli.py -l "Manchester" -d 15 --no-open
```

### Options

| Flag | Description |
|------|-------------|
| `-l`, `--location` | Starting location — place name or address (required) |
| `-d`, `--distance` | Target distance in km (required) |
| `--prefer` | Route preference, e.g. `flat`, `scenic`, `avoid busy roads` |
| `--variants N` | Generate N route variants shown on the same map in different colours |
| `--no-open` | Don't automatically open the map in a browser |

## Output

Generated files are saved in the `output/` directory:

- `route_*.html` — interactive map you can open in any browser
- `route_*.gpx` — GPX file for loading into Garmin, Strava, Komoot, etc.
