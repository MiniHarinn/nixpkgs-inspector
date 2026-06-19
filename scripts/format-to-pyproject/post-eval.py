import json
from collections import defaultdict

from nipylib import getEvalResult


def main():
    collected = getEvalResult()

    packages = defaultdict(list)
    for entry in collected:
        packages[entry["position"]].append(entry)

    attrs = [x["attrpath"] for p in packages.values() for x in p]
    print(json.dumps(attrs, indent=2))


if __name__ == "__main__":
    main()
