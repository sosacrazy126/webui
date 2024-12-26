
{ pkgs }: {
  deps = [
    pkgs.python310
    pkgs.poetry
    pkgs.nodePackages.npm
    pkgs.bashInteractive
    pkgs.man
    pkgs.git
  ];
}
