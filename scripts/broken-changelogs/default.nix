{ nilib, ... }:
{
  script = {
    builder = nilib.packagesWith;

    collect = pkg: attrpath: { inherit (pkg.meta) changelog; };

    predicate = _: pkg:
      # TODO: nilib.hasDeepAttr pkg "meta.changelog"
      with builtins; (hasAttr "meta" pkg) && (hasAttr "changelog" pkg.meta);
  };

  # TODO: should use this attr for postEval, maybe should be runCommand?
  postEval = ./post-eval.py;

  meta = {
    description = "Check if changelogs are usable";
    trackingIssue = 514132;
    scheduled = false; # slow
  };
}
