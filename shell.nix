{
  pkgs ? import <nixpkgs> { },
}:
pkgs.mkShell {
  nativeBuildInputs = with pkgs.buildPackages; [
    python3
    python3Packages.cairosvg
    python3Packages.drawsvg
    python3Packages.ephem
    python3Packages.pypdf2
    python3Packages.reportlab
    svg2pdf
    pdftk
  ];
}
