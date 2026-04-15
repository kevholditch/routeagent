"""CLI entry point for the route planning agent."""

import argparse
import sys
import webbrowser

from dotenv import load_dotenv

load_dotenv(override=True)

from agent.core import run_agent
from agent.prompts import build_user_message


def main() -> None:
    parser = argparse.ArgumentParser(description="Plan a circular running route.")
    parser.add_argument(
        "-l", "--location", required=True, help="Starting location (place name or address)"
    )
    parser.add_argument(
        "-d", "--distance", required=True, type=float, help="Target distance in km"
    )
    parser.add_argument(
        "--prefer", default=None, help="Route preference, e.g. 'flat', 'scenic', 'avoid busy roads'"
    )
    parser.add_argument(
        "--variants",
        type=int,
        default=None,
        help="Generate N route variants on the same map",
    )
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="Don't open the map in a browser",
    )
    args = parser.parse_args()

    user_message = build_user_message(
        location=args.location,
        distance_km=args.distance,
        preferences=args.prefer,
        variants=args.variants,
    )

    print(f"Planning a {args.distance} km route from {args.location}...\n", file=sys.stderr)
    # run_agent streams text to stderr as it goes — no need to re-print it.
    run_agent(user_message)

    # Try to find and open the generated map
    if not args.no_open:
        _open_latest_map()


def _open_latest_map() -> None:
    """Open the most recently generated HTML map in the default browser."""
    from pathlib import Path

    output_dir = Path(__file__).parent / "output"
    if not output_dir.exists():
        return
    html_files = sorted(output_dir.glob("route_*.html"), reverse=True)
    if html_files:
        webbrowser.open(f"file://{html_files[0].resolve()}")


if __name__ == "__main__":
    main()
