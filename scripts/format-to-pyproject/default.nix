{ nilib, ... }:
{
  script = {
    builder = nilib.packagesWith;

    predicate = _: pkg:
      (builtins.hasAttr "pyproject" pkg) && (pkg.pyproject == null);
  };

  # TODO: should use this attr for postEval, maybe should be runCommand?
  postEval = ./post-eval.py;

  meta = {
    description = "All packages that need to upgrade from format -> pyproject";
    trackingIssue = 515974;
    scheduled = true;
  };
}
