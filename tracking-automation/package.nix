{
  python3,
}:
python3.pkgs.buildPythonApplication {
  pname = "tracking-automation";
  version = "0.4.0";
  pyproject = true;
  src = ./.;

  build-system = [ python3.pkgs.uv-build ];

  dependencies = [ python3.pkgs.pygithub ];

  postInstall = ''
    cp nix/*.nix $out/${python3.sitePackages}/tracking_automation/
  '';

  pythonImportsCheck = [
    "tracking_automation"
    "tracking_automation.github"
  ];
  doCheck = false;

  meta = {
    description = "Frozen-universe nixpkgs tracking-issue automation";
    mainProgram = "tracking-automation";
  };
}
