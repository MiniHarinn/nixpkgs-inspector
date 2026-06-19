{ lib, nilib, ... }:
{
  script = {
    builder = nilib.packagesWith;

    predicate = _: pkg:
      with builtins; (
        (hasAttr "meta" pkg)
        && (hasAttr "description" pkg.meta)
        && (lib.strings.hasSuffix "." pkg.meta.description)
      );
  };

  meta = {
    description = "Does not respect meta.description requirements";
    scheduled = true;
  };
}
