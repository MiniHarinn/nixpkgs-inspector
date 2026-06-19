#! /usr/bin/env nix-shell
#! nix-shell -i python3 -p "python3.withPackages (p: [ p.requests ])"

# TODO: adapt

import json
import sys
import requests
from typing import TypedDict

class PackageInfo(TypedDict):
    attrpath: str
    key: str
    changelog: str
    maintainers: list[str]
    status: str | None


def check_links():
    raw = sys.stdin.read()
    data: list[PackageInfo] = json.loads(raw)

    results = data

    for entry in data:
        ap = entry['attrpath']

        try:
            response = requests.get(entry['changelog'], timeout=10, allow_redirects=True)
            status = str(response.status_code)
        except requests.RequestException:
            status = "000"

        print(f"[{status}]", ap)
        if status == "200":
            results = [r for r in results if r['attrpath'] != ap]

        entry['status'] = status

        with open('checked.json', 'w+') as f:
            json.dump(results, f, indent=2)


if __name__ == "__main__":
    check_links()
