{ lib, nilib, ... }:
{
  script = {
    builder = cond: prefix: set:
      (builtins.foldl' (acc: e:
        if e.position == null || builtins.hasAttr e.position acc.seen then
          acc
        else
          {
            seen = acc.seen // { ${e.position} = true; };
            kept = acc.kept ++ [ e ];
          }
      ) { seen = { }; kept = [ ]; } (nilib.packagesWith cond prefix set)).kept;

    predicate = _: pkg:
      with builtins; (
        (hasAttr "version" pkg)
        && (isString pkg.version)
        && (lib.strings.hasInfix "unstable" pkg.version)
        # Does not comply with pkgs/README.md "Versioning": a snapshot must be
        # "{version}-unstable-YYYY-MM-DD" with {version} starting with a digit.
        && (match "[0-9].*-unstable-[0-9]{4}-[0-9]{2}-[0-9]{2}" pkg.version == null)
      );
  };

  meta = {
    description = "Matches invalid sheme of unstable version";
    scheduled = true;
  };

  tracking-automation = {
    enable = true;
    issue = 541820;
    creationRev = "b1bd76124a60a81341f984594c945b0d591c9606";
  };
}
