{
  description = "our superrrrr aswesome nixpkgs-inspector";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";

  outputs =
    { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
      lib = pkgs.lib;

      nilib = ./lib;

      scriptNames = lib.attrNames (lib.filterAttrs (_: t: t == "directory") (builtins.readDir ./scripts));

      # Get all those config.toml and pack it into scriptsMeta
      scriptsMeta = lib.genAttrs scriptNames (
        name: builtins.fromTOML (builtins.readFile ./scripts/${name}/config.toml)
      );
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

      apps.${system} = lib.genAttrs scriptNames (name: {
        type = "app";
        program = "${
          pkgs.writeShellApplication {
            name = "script-${name}";
            runtimeInputs = [
              pkgs.python3
              pkgs.nix
            ];
            text = ''
              export NIX_PATH="nixpkgs=${nixpkgs}"
              exec python3 ${./scripts/${name}}/entry.py "$@" "${nilib}"
            '';
          }
        }/bin/script-${name}";
      });

      inherit scriptsMeta;

      # I suppose this will be useful when we have da frontend :D
      nixpkgsRev = nixpkgs.rev or "unknown";
    };
}
