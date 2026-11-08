"""Build a local Cowork plugin that uses this checkout's shared review state."""

import argparse
import json
import sys
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="Destination ZIP for this machine")
    args = parser.parse_args()
    manifest = {
        "name": "lumos-access-reviews",
        "version": "1.0.0",
        "description": "Review synthetic Lumos permissions and record confirmed decisions.",
    }
    mcp = {
        "mcpServers": {
            "lumos-access-reviews": {
                "command": Path(sys.executable).as_posix(),
                "args": [(ROOT / "server/src/main.py").as_posix(), "--assistant-host", "claude_cowork"],
            }
        }
    }
    with ZipFile(args.output, "x", ZIP_DEFLATED) as plugin:
        plugin.writestr(".claude-plugin/plugin.json", json.dumps(manifest, indent=2))
        plugin.writestr(".mcp.json", json.dumps(mcp, indent=2))
        plugin.write(ROOT / "reviewer-skill/SKILL.md", "skills/access-review/SKILL.md")
    print(args.output.resolve())


if __name__ == "__main__":
    main()
