"""Read-only access to Dana’s synthetic personal inbox."""

import argparse
import json
import re
from pathlib import Path

from mcp_stdio import obj, serve_stdio, string


CONTEXT = Path(__file__).resolve().parents[2] / "personal-workspace" / "context"
WORD = re.compile(r"[^\W_]+")
TOOLS = {
    "search_personal_context": (
        "Search Dana Morgan's simulated private work context for a named person and responsibility. "
        "Call before proposing a decision when the reviewer asks to investigate a person's access. "
        "Use the returned excerpt to inform your reasoning and keep it out of Lumos tool payloads.",
        obj(("person", "topic"), person=string(), topic=string()),
    ),
}


def search_personal_context(person, topic, use_transcript=False):
    topics = set(WORD.findall(topic.casefold()))
    messages = json.loads((CONTEXT / "inbox-index.json").read_text(encoding="utf-8"))
    matches = []
    for message in messages:
        if message["person"].casefold() != person.strip().casefold():
            continue
        if not topics.intersection(WORD.findall(" ".join(message["topics"]).casefold())):
            continue
        if use_transcript:
            content = (CONTEXT / "sales-ops-call-transcript.md").read_text(encoding="utf-8")
            excerpt = content.split("## Transcript\n", 1)[1].split("\n## Handling\n", 1)[0].strip()
            matches.append({
                "source_id": "DANA-SALES-OPS-CALL", "title": "Sales Ops transition call", "source_type": "call_transcript",
                "date": message["date"], "excerpt": excerpt, "visibility": "private_to_reviewer",
            })
            continue
        content = (CONTEXT / message["file"]).read_text(encoding="utf-8")
        excerpt = content.split("## Message\n", 1)[1].split("\n## Handling\n", 1)[0].strip()
        matches.append({
            "source_id": message["source_id"],
            "title": message["title"],
            "from": message["from"],
            "date": message["date"],
            "excerpt": excerpt,
            "visibility": "private_to_reviewer",
        })
    return {"reviewer": "Dana Morgan", "results": matches}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Synthetic reviewer work context")
    parser.add_argument("--transcript", action="store_true", help="Use the private call transcript for the ChatGPT demo")
    options = parser.parse_args()
    serve_stdio(
        "dana-personal-context",
        "Read-only synthetic work context for Dana Morgan. Use search_personal_context to check "
        "what changed in a person's duties. Keep private excerpts and source details out of Lumos payloads. "
        "Send only the policy-based decision.",
        TOOLS,
        lambda _, arguments: search_personal_context(**arguments, use_transcript=options.transcript),
    )
