import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def main():
    artifacts_dir = Path(sys.argv[1])
    meta_path = Path(sys.argv[2])
    nixpkgs_rev = sys.argv[3]

    meta = json.loads(meta_path.read_text())

    names = sorted(
        p.stem for p in artifacts_dir.glob("*.json") if p.name != "index.json"
    )

    index = {
        "generatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "nixpkgsRev": nixpkgs_rev,
        "scripts": [
            {
                "name": name,
                "trackingIssueNum": meta.get(name, {}).get("trackingIssueNum"),
                "file": f"{name}.json",
            }
            for name in names
        ],
    }

    (artifacts_dir / "index.json").write_text(json.dumps(index, indent=2) + "\n")


if __name__ == "__main__":
    main()
