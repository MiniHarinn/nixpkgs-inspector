{ nilib, ... }:
{
  script = {
    builder = nilib.packagesWith;

    predicate = _: pkg:
      (builtins.hasAttr "pyproject" pkg) && (pkg.pyproject == null);
  };

  postEval.file = ./post-eval.py;

  meta = {
    description = "All packages that need to upgrade from format -> pyproject";
    trackingIssue = 515974;
    scheduled = true;
  };
}
