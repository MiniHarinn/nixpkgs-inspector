{
  nixpkgs,
  scriptDir,
  libDir,
  configFile,
  toolingNixpkgs,
  system ? builtins.currentSystem,
}:
let
  lib = import (toolingNixpkgs + "/lib");
  nilib = import libDir { inherit lib; };
  subjectPkgs = import nixpkgs ({ inherit system; } // import configFile);
  s = (import scriptDir { inherit nilib lib; }).script;
in
s.builder s.predicate "" subjectPkgs
