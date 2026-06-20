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

      # For script's eval only, system components should ues normal `pkgs` above!!!
      subjectPkgs = import subject-nixpkgs (
        { inherit system; } // import ./lib/nixpkgs-default-config.nix
      );

      nilib = import ./lib { inherit lib; };

      # Discovery and lazy load all scripts
      loadedScripts = lib.mapAttrs (name: _: import ./scripts/${name} { inherit nilib lib; }) (
        lib.filterAttrs (_: t: t == "directory") (builtins.readDir ./scripts)
      );

      # My attempt at making 1 script = 1 drv; meta is a little noisy with stdenv stuff but it works.
      mkScript =
        name: script:
        let
          collectedJSON = pkgs.writeText "${name}-collected.json" (
            builtins.toJSON (script.script.builder script.script.predicate "" subjectPkgs)
          );

          postEval = script.postEval or null;
          hasPostEval = postEval != null;

          runner = pkgs.writeShellApplication {
            name = "script-${name}";
            runtimeInputs = if hasPostEval then [ pkgs.python3 ] else [ pkgs.coreutils ];
            text =
              if hasPostEval then
                ''
                  export PYTHONPATH=${./lib/python}''${PYTHONPATH:+:$PYTHONPATH}
                  exec python3 ${postEval} ${collectedJSON} "$@"
                ''
              else
                "exec cat ${collectedJSON}";
          };
        in
        runner.overrideAttrs (old: {
          meta =
            (old.meta or { })
            // {
              mainProgram = "script-${name}";
              trackingIssue = null;
              scheduled = false;
            }
            // (script.meta or { });
        });
    in
    {

      packages.${system} = lib.mapAttrs mkScript loadedScripts;

      nixpkgsRev = subject-nixpkgs.rev or "unknown";
    };
}
