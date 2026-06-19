{ lib, nilib, ... }:

let
  # TODO: worth nilib-ing?
  magicHackGetAttrs = pkg:
    if !(builtins.hasAttr "meta" pkg) then
      # inputDerivation dont have meta set
      {}
    else (if (builtins.hasAttr "attrs" pkg.meta) then
      pkg.meta.attrs
    # stdenv-linux dont use check-meta
    else { });

  charIsUpper = c: let v = lib.strings.charToInt c; in (v >= 65 && v <= 90) || v == 95;
    # 95 -> allow `_` in name

  isUpper = w: lib.all charIsUpper (lib.stringToCharacters w);

  hasValueThatLooksLikeEnv = pkg:
    lib.any isUpper (lib.attrNames
      # TODO: Have tracing option in cli
      (builtins.trace pkg.name (magicHackGetAttrs pkg)));

  # TODO: this represent extra data that the script collect
  # that are relevant (baseCollectedData // (collectInfo pkg attrpath))
  # might need structure enforcement?
  collectInfo = pkg: attrpath:
    {
      upper = lib.filter isUpper (lib.attrNames (magicHackGetAttrs pkg));
    };

in {
  patch = ./expose-verbatim-attrs.patch;

  script = {
    builder = nilib.packagesWith;

    predicate = _: hasValueThatLooksLikeEnv;

    collect = collectInfo;
  };

  meta = {
    description = "Find top-level env var to move in env = { ... }";
    scheduled = true;
  };
}
