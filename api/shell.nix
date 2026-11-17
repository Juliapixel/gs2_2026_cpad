{
  pkgs ? import <nixpkgs> {},
  venvDir ? "./.venv",
}: pkgs.mkShell (finalAttrs: {
  inherit venvDir;
  name = "cpad_python_env";
  buildInputs = with pkgs; [
    python3Packages.python

    python3Packages.venvShellHook

    python3Packages.numpy
    python3Packages.requests

    pyright
    taglib
    openssl
    git
    libxml2
    libxslt
    libzip
    zlib
  ];

  postVenvCreation = ''
    unset SOURCE_DATE_EPOCH
    pip install -r ${./requirements.txt}
  '';

  postShellHook = ''
    unset SOURCE_DATE_EPOCH
  '';
})
