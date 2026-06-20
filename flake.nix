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

      mkScriptApp =
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

      apps.${system} = lib.mapAttrs mkScriptApp loadedScripts;

      scriptsMeta = lib.mapAttrs (
        _: script:
        {
          trackingIssue = null;
          scheduled = false;
        }
        // (script.meta or { })
      ) loadedScripts;

      nixpkgsRev = subject-nixpkgs.rev or "unknown";
    };
}
