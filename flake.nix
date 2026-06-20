{
  description = "our superrrrr aswesome nixpkgs-inspector";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    subject-nixpkgs.url = "github:NixOS/nixpkgs/master"; # For script's package set; will be overwritten (re-lock) in ci for newest revision before every run.
  };

  outputs =
    {
      self,
      nixpkgs,
      subject-nixpkgs,
    }:
    let
      system = "x86_64-linux";

      pkgs = nixpkgs.legacyPackages.${system};
      lib = pkgs.lib;

      nilib = import ./lib { inherit lib; };

      # The packaged tracking engine (one-shot, args-driven).
      tracking-automation = pkgs.callPackage ./tracking-automation/package.nix { };

      # Discovery and lazy load all scripts
      loadedScripts = lib.mapAttrs (name: _: import ./scripts/${name} { inherit nilib lib; }) (
        lib.filterAttrs (_: t: t == "directory") (builtins.readDir ./scripts)
      );

      # My attempt at making 1 script = 1 drv; meta is a little noisy with stdenv stuff but it works.
      mkScript =
        name: script:
        let
          collectedJSON = pkgs.writeText "${name}-collected.json" (
            builtins.toJSON (import ./lib/eval.nix {
              nixpkgsSrc = subject-nixpkgs;
              scriptDir = ./scripts/${name};
              configFile = ./lib/nixpkgs-default-config.nix;
              toolingNixpkgs = pkgs.path;
              inherit system;
            }).collect
          );

          hasPostEval = script ? postEval;
          postEval =
            if hasPostEval then
              {
                impure = false;
                pythonDeps = _: [ ];
              }
              // script.postEval
            else
              null;

          python = if hasPostEval then pkgs.python3.withPackages postEval.pythonDeps else null;

          # Pure post-eval: this will most of the time gets us there, if postEval only do some trivial transformation
          pureResult = pkgs.runCommand "${name}-result.json" { nativeBuildInputs = [ python ]; } ''
            export PYTHONPATH=${./lib/python}''${PYTHONPATH:+:$PYTHONPATH}
            python3 ${postEval.file} ${collectedJSON} > $out
          '';

          # Impure runs python at run time (needs network), opt in
          impure = hasPostEval && postEval.impure;

          runner = pkgs.writeShellApplication {
            name = "script-${name}";
            runtimeInputs = if impure then [ python ] else [ pkgs.coreutils ];
            text =
              if impure then
                ''
                  export PYTHONPATH=${./lib/python}''${PYTHONPATH:+:$PYTHONPATH}
                  exec python3 ${postEval.file} ${collectedJSON} "$@"
                ''
              else
                "exec cat ${if hasPostEval then pureResult else collectedJSON}";
          };

          ta = script.tracking-automation or { };

          # Tracking issue automation entry point
          trackingApp = pkgs.writeShellApplication {
            name = "${name}-run-tracking-automation";
            runtimeInputs = [
              pkgs.git
              pkgs.nix
            ];
            text = ''
              exec ${lib.getExe tracking-automation} \
                --script ${name} \
                --issue ${toString ta.issue} \
                --creation-rev ${ta.creationRev} \
                --script-dir ${./scripts/${name}} \
                --lib-dir ${./lib} \
                --config-file ${./lib/nixpkgs-default-config.nix} \
                --tooling-nixpkgs ${pkgs.path} \
                "$@"
            '';
          };
        in
        runner.overrideAttrs (old: {
          meta =
            (old.meta or { })
            // {
              mainProgram = "script-${name}";
              scheduled = false;
            }
            // (script.meta or { });
          passthru =
            (old.passthru or { })
            // lib.optionalAttrs (ta.enable or false) {
              tracking-automation = ta // { run = trackingApp; };
            };
        });
    in
    {

      packages.${system} = (lib.mapAttrs mkScript loadedScripts) // {
        inherit tracking-automation;
      };

      nixpkgsRev = subject-nixpkgs.rev or "unknown";
    };
}
