{ nilib, ... }:
{
  script = {
    builder = nilib.packagesWith;

    collect = pkg: attrpath: { inherit (pkg.meta) changelog; };

    predicate =
      _: pkg:
      # TODO: nilib.hasDeepAttr pkg "meta.changelog"
      with builtins;
      (hasAttr "meta" pkg) && (hasAttr "changelog" pkg.meta);
  };

  postEval = {
    file = ./post-eval.py;
    impure = true; # network request, duh 🤷‍♀
    pythonDeps = p: [ p.requests ];
  };

  meta = {
    description = "Check if changelogs are usable";
    scheduled = false; # slow
  };

  tracking-automation = {
    issue = 514132;
  };
}
