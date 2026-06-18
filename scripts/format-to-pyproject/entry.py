import json
import subprocess
from collections import defaultdict
from pathlib import Path

import sys


def main():
    script_dir = Path(__file__).parent
    collect_nix = script_dir / "collect-packages.nix"

    nilib_path = sys.argv[1]

    expr = f"""
      let
        defaultNixpkgsConfig = import {nilib_path}/nixpkgs-default-config.nix;

        pkgs = import <nixpkgs> defaultNixpkgsConfig;

        nilib = import {nilib_path} {{ inherit (pkgs) lib; }};

        result = import {collect_nix} {{
          inherit pkgs nilib;
        }};
      in result
    """

    result = subprocess.run(
        ["nix", "eval", "--impure", "--json", "--expr", expr, "-vv"],
        capture_output=True,
        text=True,
        check=True,
    )

    output = json.loads(result.stdout)

    packages = defaultdict(list)
    for entry in output:
        packages[entry["position"]].append(entry)

    attrs = [x["attrpath"] for p in packages.values() for x in p]
    print(json.dumps(attrs, indent=2))


if __name__ == "__main__":
    main()
