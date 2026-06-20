# Single source of truth for evaluating a script against a subject nixpkgs.
# Both the flake (build-time, against the pinned input) and tracking-automation
# (runtime, against arbitrary worktree revs) go through here.
{
  nixpkgsSrc,
  scriptDir,
  configFile,
  toolingNixpkgs,
  system ? builtins.currentSystem,
}:
let
  lib = import (toolingNixpkgs + "/lib");
  nilib = import ./. { inherit lib; };
  subjectPkgs = import nixpkgsSrc ({ inherit system; } // import configFile);

  s = (import scriptDir { inherit nilib lib; }).script;

  collect = s.builder s.predicate "" subjectPkgs;

  check =
    attrs:
    let
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
          ok = builtins.tryEval (p != null && lib.isDerivation p && s.predicate a p);
        in
        ok.success && ok.value
      ) attrs;
    in
    lib.concatStringsSep "\n" still;
in
{
  inherit collect check;
}
