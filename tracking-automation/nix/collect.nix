{
  nixpkgs,
  scriptDir,
  libDir,
  configFile,
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
}).collect
