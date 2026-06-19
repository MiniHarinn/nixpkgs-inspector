{ lib, nilib, ... }:
{
  script = {
    builder = nilib.packagesWith;

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
}
