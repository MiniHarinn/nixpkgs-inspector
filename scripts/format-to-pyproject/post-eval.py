import json
import sys
from collections import defaultdict
from pathlib import Path


def main():
    collected = json.loads(Path(sys.argv[1]).read_text())

    packages = defaultdict(list)
    for entry in collected:
        packages[entry["position"]].append(entry)

    attrs = [x["attrpath"] for p in packages.values() for x in p]
    print(json.dumps(attrs, indent=2))


if __name__ == "__main__":
    main()
