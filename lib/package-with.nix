{ lib }:
let
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
                  position = pkg.meta.position or null; # Sadly, some weird derivation does not have meta / not literal 🥲
                  maintainers = builtins.map (m: m.github) pkg.meta.maintainers;
                }
              ]
            else if pkg.recurseForDerivations or false || pkg.recurseForRelease or false then
              packagesWith cond "${name}." pkg
            else
              [ ]
          );
        in
        if result.success then result.value else [ ]
      ) set
    ));
in
{
  inherit packagesWith;
}
