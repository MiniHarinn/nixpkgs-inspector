{
  description = "our superrrrr aswesome nixpkgs-inspector";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";

  outputs =
    { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};

      nilib = ./lib;
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

      apps.${system} = builtins.mapAttrs (name: _: {
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
      }) (pkgs.lib.filterAttrs (_: t: t == "directory") (builtins.readDir ./scripts));
    };
}
