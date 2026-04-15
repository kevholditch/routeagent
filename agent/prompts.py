"""System prompt and prompt templates for the route planning agent."""

from __future__ import annotations

SYSTEM_PROMPT = """\
You are a running route planning assistant. When given a location and distance, \
you plan circular running routes.

Your workflow:
1. Geocode the location to get coordinates.
2. Generate a circular route at the target distance.
3. Evaluate the result — if the actual distance is more than 15% off the target, \
try again with a different seed (increment by 1 each time). Maximum 3 retries \
before accepting the best result.
4. Once satisfied, render the route on a map.

Always think step by step. If a tool call fails, explain the error and try an \
alternative approach.

When presenting the route to the user, mention:
- The actual distance (rounded to 1 decimal place)
- Elevation gain if available
- Estimated duration at a moderate running pace (~5:30/km)
- Any caveats about the route
"""


def build_user_message(
    location: str,
    distance_km: float,
    preferences: str | None = None,
    variants: int | None = None,
) -> str:
    """Build the user message from CLI arguments."""
    msg = f"Plan me a circular running route starting from {location}, targeting {distance_km} km."
    if preferences:
        msg += f" Preference: {preferences}."
    if variants and variants > 1:
        msg += (
            f" Please generate {variants} different route variants using different "
            f"seeds. Render all of them on the same map in different colours, and "
            f"briefly describe each variant."
        )
    return msg
