{ lib }:
let
  packagesWith = import ./package-with.nix { inherit lib; };
in {
  inherit (packagesWith) packagesWith;
}
