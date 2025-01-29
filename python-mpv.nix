# python-mpv.nix
{
  lib,
  stdenv,
  buildPythonPackage,
  fetchFromGitHub,
  setuptools,
  wheel,
  mpv,
}:

buildPythonPackage rec {
    pname = "python-mpv";
    version = "1.0.6";

    src = fetchFromGitHub {
        owner = "jaseg";
        repo = "python-mpv";
        rev = "v${version}";
        sha256 = "1axVJ8XXs0ZPgsVux3+6YUm1KttLceZyyHOuUEHIFl4=";
    };

    doCheck = false;
    pythonImportsCheck = [ "mpv" ];

    buildPhase = ''
        touch ./os-release
        mkdir ./dist
    '';
         postPatch = ''
    substituteInPlace mpv.py \
      --replace "sofile = ctypes.util.find_library('mpv')" \
                'sofile = "${mpv}/lib/libmpv${stdenv.hostPlatform.extensions.sharedLibrary}"'
  '';

    format = "setuptools";
    nativeBuildInputs = [
       setuptools
       wheel
       
    ];

    buildInputs = [
        mpv
    ];
}