{
  pkgs ? import <nixpkgs> { },
}:
pkgs.mkShell {
  nativeBuildInputs = with pkgs.buildPackages; [
    python3
    python3Packages.drawsvg
    python3Packages.ephem
    python3Packages.reportlab
  ];
}
