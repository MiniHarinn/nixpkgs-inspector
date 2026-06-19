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

      scriptNames = lib.attrNames (lib.filterAttrs (_: t: t == "directory") (builtins.readDir ./scripts));

      scriptsMeta = lib.genAttrs scriptNames (
        name:
        let
          configPath = ./scripts/${name}/config.toml;
          defaults = {
            trackingIssueNum = null;
            scheduled = false;
          };
        in
        defaults // (if builtins.pathExists configPath then builtins.fromTOML (builtins.readFile configPath) else { })
      );

      collectedJSON = lib.genAttrs scriptNames (
        name:
        pkgs.writeText "${name}-collected.json" (
          builtins.toJSON (
            import ./scripts/${name}/collect.nix {
              pkgs = subjectPkgs;
              inherit nilib;
            }
          )
        )
      );

      mkScriptApp =
        name:
        let
          postEval = ./scripts/${name}/post-eval.py;
          hasPostEval = builtins.pathExists postEval;

          runner = pkgs.writeShellApplication {
            name = "script-${name}";
            runtimeInputs = if hasPostEval then [ pkgs.python3 ] else [ pkgs.coreutils ];
            text =
              if hasPostEval then
                ''
                  export PYTHONPATH=${./lib/python}''${PYTHONPATH:+:$PYTHONPATH}
                  exec python3 ${postEval} ${collectedJSON.${name}} "$@"
                ''
              else
                "exec cat ${collectedJSON.${name}}";
          };
        in
        {
          type = "app";
          program = lib.getExe runner;
        };
    in
    {
      devShells.${system}.default = pkgs.mkShell {
        packages = [
          pkgs.python314
          pkgs.uv
        ];
        shellHook = ''
          export UV_PYTHON_PREFERENCE=only-system
        '';
      };

      apps.${system} = lib.genAttrs scriptNames mkScriptApp;

      inherit scriptsMeta;

      nixpkgsRev = subject-nixpkgs.rev or "unknown";
    };
}
