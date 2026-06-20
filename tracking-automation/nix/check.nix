{
  nixpkgs,
  scriptDir,
  libDir,
  configFile,
  attrs,
  toolingNixpkgs,
  system ? builtins.currentSystem,
}:
(import (libDir + "/eval.nix") {
  nixpkgsSrc = nixpkgs;
  inherit
    scriptDir
    configFile
    toolingNixpkgs
    system
    ;
}).check attrs
