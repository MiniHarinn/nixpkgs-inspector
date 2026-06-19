{ pkgs, nilib }:
let
  predicate = pkg:
    (builtins.hasAttr "pyproject" pkg)
    && (pkg.pyproject == null);
in
nilib.packagesWith (name: pkg: predicate pkg) "" pkgs
