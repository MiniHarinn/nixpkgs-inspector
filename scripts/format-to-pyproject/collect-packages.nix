{ pkgs }:
let
  # Borrowed from maintainers/scripts/check-hydra-by-maintainer.nix
  inherit (pkgs) lib;

  packagesWith =
    cond: prefix: set:
    (lib.flatten (
      lib.mapAttrsToList (
        name: pkg:
        let
          result = builtins.tryEval (
            if lib.isDerivation pkg && cond name pkg then
              [
                {
                  attrpath = "${prefix}${name}";
                  inherit (pkg.meta) position;
                  maintainers = builtins.map (m: m.github) pkg.meta.maintainers;
                }
              ]
            else if
              pkg.recurseForDerivations or false || pkg.recurseForRelease or false
            # then packagesWith cond return pkg
            then
              packagesWith cond "${name}." pkg
            else
              [ ]
          );
        in
        if result.success then result.value else [ ]
      ) set
    ));

in
packagesWith (name: pkg: ((builtins.hasAttr "pyproject" pkg) && (pkg.pyproject == null))) "" pkgs
