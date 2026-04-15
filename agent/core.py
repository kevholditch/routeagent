"""Agent loop — the central orchestrator."""

from __future__ import annotations

import json
import sys

import anthropic

from agent.prompts import SYSTEM_PROMPT
from agent.tool_handlers import dispatch_tool
from agent.tools import TOOLS

MODEL = "claude-sonnet-4-6"

MAX_ITERATIONS = 10


def run_agent(user_message: str, stream: bool = True) -> str:
    """Run the agent loop until Claude produces a final text response.

    Args:
        user_message: The user's request.
        stream: If True, stream text output to stdout in real-time.

    Returns:
        Claude's final text response.
    """
    client = anthropic.Anthropic()
    messages: list[dict] = [{"role": "user", "content": user_message}]

    for _ in range(MAX_ITERATIONS):
        if stream:
            response = _stream_response(client, messages)
        else:
            response = client.messages.create(
                model=MODEL,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages,
            )

        # Append assistant response to conversation
        messages.append({"role": "assistant", "content": response.content})

        # Check if there are any tool_use blocks
        tool_uses = [b for b in response.content if b.type == "tool_use"]
        if not tool_uses:
            # No tool calls — extract final text and return
            text_parts = [b.text for b in response.content if b.type == "text"]
            return "\n".join(text_parts)

        # Execute each tool and collect results
        tool_results = []
        for tool_use in tool_uses:
            if stream:
                print(f"\n⚙  Running {tool_use.name}...", file=sys.stderr)
            result_str = dispatch_tool(tool_use.name, tool_use.input)
            if stream:
                _print_tool_summary(tool_use.name, result_str)
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": result_str,
                }
            )

        messages.append({"role": "user", "content": tool_results})

    return "Agent reached maximum iterations without completing."


def _stream_response(
    client: anthropic.Anthropic,
    messages: list[dict],
) -> anthropic.types.Message:
    """Stream a response, printing text chunks in real-time."""
    with client.messages.stream(
        model=MODEL,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        tools=TOOLS,
        messages=messages,
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True, file=sys.stderr)
        print(file=sys.stderr)  # newline after streamed text
        return stream.get_final_message()


def _print_tool_summary(tool_name: str, result_str: str) -> None:
    """Print a brief summary of a tool result."""
    try:
        data = json.loads(result_str)
    except json.JSONDecodeError:
        return

    if "error" in data:
        print(f"   ✗ Error: {data['error']}", file=sys.stderr)
        return

    if tool_name == "geocode_location":
        print(
            f"   ✓ Found: {data.get('display_name')} "
            f"({data.get('lat'):.4f}, {data.get('lon'):.4f})",
            file=sys.stderr,
        )
    elif tool_name == "generate_circular_route":
        print(
            f"   ✓ Route: {data.get('actual_distance_km')} km, "
            f"elevation gain: {data.get('elevation_gain_m', 'N/A')} m",
            file=sys.stderr,
        )
    elif tool_name == "render_route_map":
        print(f"   ✓ Map saved: {data.get('file_path')}", file=sys.stderr)
    elif tool_name == "export_gpx":
        print(f"   ✓ GPX saved: {data.get('file_path')}", file=sys.stderr)
    else:
        print("   ✓ Done", file=sys.stderr)
