{ nilib, ... }:
{
  script = {
    builder = nilib.packagesWith;

    predicate = _: pkg: (builtins.hasAttr "pyproject" pkg) && (pkg.pyproject == null);
  };

  # postEval.file = ./post-eval.py; # USELESS

  meta = {
    description = "All packages that need to upgrade from format -> pyproject";
    scheduled = true;
  };

  tracking-automation = {
    enable = false;
    issue = 515974;
    creationRev = "304246fb630fc9b6a49b20e534940950c0664f53"; # Superrr important: its a nixpkgs' rev where tracking issue list was snapshotted!
  };
}
