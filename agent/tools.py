"""Tool definitions for the route planning agent (Anthropic tool-use schema)."""

TOOLS: list[dict] = [
    {
        "name": "geocode_location",
        "description": "Convert a place name or address into latitude/longitude coordinates.",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "Place name or address, e.g. 'Cambourne, Cambridge'",
                }
            },
            "required": ["location"],
        },
    },
    {
        "name": "generate_circular_route",
        "description": (
            "Generate a circular running route starting and ending at the given "
            "coordinates, targeting a specific distance."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "lat": {
                    "type": "number",
                    "description": "Start latitude",
                },
                "lon": {
                    "type": "number",
                    "description": "Start longitude",
                },
                "target_distance_km": {
                    "type": "number",
                    "description": "Desired route distance in kilometres",
                },
                "seed": {
                    "type": "integer",
                    "description": (
                        "Random seed for route variation. Different seeds produce "
                        "different routes. Default: 42"
                    ),
                },
            },
            "required": ["lat", "lon", "target_distance_km"],
        },
    },
    {
        "name": "render_route_map",
        "description": "Render a route on an interactive map and save it as an HTML file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "coordinates": {
                    "type": "array",
                    "items": {
                        "type": "array",
                        "items": {"type": "number"},
                    },
                    "description": "Route geometry as array of [lon, lat] pairs",
                },
                "start_lat": {
                    "type": "number",
                    "description": "Start point latitude",
                },
                "start_lon": {
                    "type": "number",
                    "description": "Start point longitude",
                },
                "distance_km": {
                    "type": "number",
                    "description": "Actual route distance in km",
                },
                "location_name": {
                    "type": "string",
                    "description": "Human-readable location name for the map title",
                },
            },
            "required": [
                "coordinates",
                "start_lat",
                "start_lon",
                "distance_km",
                "location_name",
            ],
        },
    },
    {
        "name": "get_elevation_profile",
        "description": "Get the elevation profile for a route to assess hilliness.",
        "input_schema": {
            "type": "object",
            "properties": {
                "coordinates": {
                    "type": "array",
                    "items": {
                        "type": "array",
                        "items": {"type": "number"},
                    },
                    "description": "Route geometry as array of [lon, lat] pairs",
                }
            },
            "required": ["coordinates"],
        },
    },
    {
        "name": "export_gpx",
        "description": "Export a route as a GPX file for loading into running watches and apps.",
        "input_schema": {
            "type": "object",
            "properties": {
                "coordinates": {
                    "type": "array",
                    "items": {
                        "type": "array",
                        "items": {"type": "number"},
                    },
                    "description": "Route geometry as array of [lon, lat] pairs",
                },
                "location_name": {
                    "type": "string",
                    "description": "Human-readable location name for the GPX metadata",
                },
                "distance_km": {
                    "type": "number",
                    "description": "Route distance in km",
                },
            },
            "required": ["coordinates", "location_name", "distance_km"],
        },
    },
]
