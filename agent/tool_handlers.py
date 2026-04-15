"""Tool implementations — actual API calls and local operations."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

import gpxpy
import gpxpy.gpx
import requests
from jinja2 import Environment, FileSystemLoader

ORS_API_KEY = os.environ.get("ORS_API_KEY", "")
ORS_BASE = "https://api.openrouteservice.org"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = PROJECT_ROOT / "templates"
OUTPUT_DIR = PROJECT_ROOT / "output"


def geocode_location(location: str) -> dict:
    """Geocode a place name to lat/lon using OpenRouteService."""
    resp = requests.get(
        f"{ORS_BASE}/geocode/search",
        params={"api_key": ORS_API_KEY, "text": location, "size": 1},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()

    features = data.get("features", [])
    if not features:
        return {"error": f"No results found for '{location}'."}

    feat = features[0]
    coords = feat["geometry"]["coordinates"]  # [lon, lat]
    label = feat["properties"].get("label", location)
    return {"lat": coords[1], "lon": coords[0], "display_name": label}


def generate_circular_route(
    lat: float,
    lon: float,
    target_distance_km: float,
    seed: int = 42,
) -> dict:
    """Generate a circular route via the ORS directions round-trip option."""
    body = {
        "coordinates": [[lon, lat]],
        "options": {
            "round_trip": {
                "length": target_distance_km * 1000,
                "points": 5,
                "seed": seed,
            }
        },
        "elevation": True,
        "instructions": False,
    }
    # Request GeoJSON format directly — avoids decoding encoded polylines,
    # which can break when elevation=True produces 3D polylines.
    resp = requests.post(
        f"{ORS_BASE}/v2/directions/foot-walking/geojson",
        json=body,
        headers={
            "Authorization": ORS_API_KEY,
            "Content-Type": "application/json",
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()

    feature = data["features"][0]
    geometry = feature["geometry"]
    properties = feature["properties"]
    summary = properties["summary"]

    # GeoJSON gives us a LineString with [lon, lat] or [lon, lat, elevation] coords
    coordinates = geometry["coordinates"]

    elevation_gain = _extract_elevation_gain(properties)

    actual_distance_km = round(summary["distance"] / 1000, 2)
    duration_minutes = round(summary["duration"] / 60, 1)

    return {
        "coordinates": coordinates,
        "actual_distance_km": actual_distance_km,
        "elevation_gain_m": elevation_gain,
        "estimated_duration_minutes": duration_minutes,
    }


def _extract_elevation_gain(properties: dict) -> float | None:
    """Try to extract total ascent from the route properties."""
    # ORS includes 'ascent' in summary when elevation=True.
    # Fallback: compute from extras/segments or return None.
    try:
        return round(properties["ascent"], 1)
    except (KeyError, TypeError):
        pass
    try:
        return round(properties["summary"]["ascent"], 1)
    except (KeyError, TypeError):
        return None


def get_elevation_profile(coordinates: list[list[float]]) -> dict:
    """Get elevation profile for a set of coordinates using ORS elevation API."""
    # Sample coordinates to stay within API limits (max ~100 points)
    sampled = _sample_coordinates(coordinates, max_points=100)

    body = {
        "format_in": "polyline",
        "format_out": "polyline",
        "geometry": [[c[0], c[1]] for c in sampled],
    }
    resp = requests.post(
        f"{ORS_BASE}/elevation/line",
        json=body,
        headers={
            "Authorization": ORS_API_KEY,
            "Content-Type": "application/json",
        },
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()

    geometry_3d = data.get("geometry", [])
    elevations = [pt[2] for pt in geometry_3d if len(pt) >= 3]

    if not elevations:
        return {"error": "No elevation data returned."}

    total_ascent = 0.0
    total_descent = 0.0
    for i in range(1, len(elevations)):
        diff = elevations[i] - elevations[i - 1]
        if diff > 0:
            total_ascent += diff
        else:
            total_descent += abs(diff)

    return {
        "elevation_profile": elevations,
        "total_ascent_m": round(total_ascent, 1),
        "total_descent_m": round(total_descent, 1),
        "max_elevation_m": round(max(elevations), 1),
        "min_elevation_m": round(min(elevations), 1),
    }


def _sample_coordinates(
    coords: list[list[float]], max_points: int = 100
) -> list[list[float]]:
    """Evenly sample coordinates down to max_points."""
    if len(coords) <= max_points:
        return coords
    step = len(coords) / max_points
    return [coords[int(i * step)] for i in range(max_points)]


def render_route_map(
    coordinates: list[list[float]],
    start_lat: float,
    start_lon: float,
    distance_km: float,
    location_name: str,
    elevation_gain_m: float | None = None,
    estimated_duration: str | None = None,
) -> dict:
    """Render the route on a Leaflet map and save as HTML."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Convert [lon, lat] -> [lat, lon] for Leaflet
    leaflet_coords = [[c[1], c[0]] for c in coordinates]

    if estimated_duration is None:
        mins = distance_km * 5.5
        estimated_duration = f"{int(mins // 60)}h {int(mins % 60):02d}m" if mins >= 60 else f"{int(mins)}m"

    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    template = env.get_template("route_map.html")
    html = template.render(
        coordinates_json=json.dumps(leaflet_coords),
        start_lat=start_lat,
        start_lon=start_lon,
        distance_km=round(distance_km, 1),
        location_name=location_name,
        elevation_gain_m=elevation_gain_m or "N/A",
        estimated_duration=estimated_duration,
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"route_{timestamp}.html"
    filepath = OUTPUT_DIR / filename
    filepath.write_text(html)
    return {"file_path": str(filepath)}


def export_gpx(
    coordinates: list[list[float]],
    location_name: str,
    distance_km: float,
) -> dict:
    """Export route as a GPX file."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    gpx = gpxpy.gpx.GPX()
    gpx.name = f"Running route — {location_name} ({distance_km} km)"

    track = gpxpy.gpx.GPXTrack()
    track.name = gpx.name
    gpx.tracks.append(track)

    segment = gpxpy.gpx.GPXTrackSegment()
    track.segments.append(segment)

    for coord in coordinates:
        # coord is [lon, lat] or [lon, lat, ele]
        lon, lat = coord[0], coord[1]
        ele = coord[2] if len(coord) >= 3 else None
        segment.points.append(gpxpy.gpx.GPXTrackPoint(lat, lon, elevation=ele))

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"route_{timestamp}.gpx"
    filepath = OUTPUT_DIR / filename
    filepath.write_text(gpx.to_xml())
    return {"file_path": str(filepath)}


# Registry mapping tool names to handler functions
TOOL_REGISTRY: dict[str, callable] = {
    "geocode_location": geocode_location,
    "generate_circular_route": generate_circular_route,
    "render_route_map": render_route_map,
    "get_elevation_profile": get_elevation_profile,
    "export_gpx": export_gpx,
}


def dispatch_tool(name: str, arguments: dict) -> str:
    """Dispatch a tool call by name, returning the JSON result string."""
    handler = TOOL_REGISTRY.get(name)
    if handler is None:
        return json.dumps({"error": f"Unknown tool: {name}"})
    try:
        result = handler(**arguments)
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": f"{type(e).__name__}: {e}"})
