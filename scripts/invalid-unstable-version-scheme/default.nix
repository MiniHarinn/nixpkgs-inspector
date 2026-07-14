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
        /* do not comply with: */
        && !(let
          split = lib.strings.splitString "-" pkg.version;
        in
          ((lib.lists.length split) == 5)
          && (lib.strings.hasPrefix "unstable" (elemAt split 1))
          && ((stringLength (elemAt split 2)) == 4)
          && ((stringLength (elemAt split 3)) == 2)
          && ((stringLength (elemAt split 4)) == 2)
        )
      );
  };

  meta = {
    description = "Matches invalid sheme of unstable version";
    scheduled = true;
  };

  tracking-automation = {
    enable = true;
    issue = 0; # TODO: real tracking issue number.
    creationRev = "b1bd76124a60a81341f984594c945b0d591c9606";
  };
}
