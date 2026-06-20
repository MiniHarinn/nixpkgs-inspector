{
  nixpkgs,
  scriptDir,
  libDir,
  configFile,
  attrs,
  toolingNixpkgs,
  system ? builtins.currentSystem,
}:
let
  lib = import (toolingNixpkgs + "/lib");
  nilib = import libDir { inherit lib; };
  subjectPkgs = import nixpkgs ({ inherit system; } // import configFile);

  pred = (import scriptDir { inherit nilib lib; }).script.predicate;

  resolve =
    a:
    let
      r = builtins.tryEval (lib.attrByPath (lib.splitString "." a) null subjectPkgs);
    in
    if r.success then r.value else null;

  still = builtins.filter (
    a:
    let
      p = resolve a;
      ok = builtins.tryEval (p != null && lib.isDerivation p && pred a p);
    in
    ok.success && ok.value
  ) attrs;
in
lib.concatStringsSep "\n" still
