{
  description = "A flake for the LISTEN.tui application";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/release-24.11";

  outputs = { self, nixpkgs, ...}:
  let
    system = "x86_64-linux";

    overlay = final: prev: {
        python311Packages = prev.python311Packages.override {
            overrides = self: super: {
            markdownify = super.markdownify.overrideAttrs (old: {
                version = "0.11.6";
                src = final.fetchPypi {
                    pname = "markdownify";
                    version = "0.11.6";
                    sha256 = "AJskDgyfTI6vHQhWJdzUAR4S8PjOxV3t+epvdlXkm/4=";
                };
            });

            psutil = super.psutil.overrideAttrs (old: {
                version = "5.9.5";
                src = final.fetchPypi {
                    pname = "psutil";
                    version = "5.9.5";
                    sha256 = "VBBjjk3znFTZV/xRzgMEis2ObWCrwPUQevUeX7Vm6zw=";
                };
                patches = [];
                patchPhase = "";
                postPatch = "";
            });

            websockets = super.websockets.overrideAttrs (old: {
                version = "11.0.3";
                src = final.fetchPypi {
                    pname = "websockets";
                    version = "11.0.3";
                    sha256 = "iPxR2aJrEPwzG+NE8XgSJKN1t4SI/DQ2IBhOlaSycBY=";
                };
                #nativeBuildInputs = [ pkgs.python311Packages.pytestCheckHook ];
                # checkPhase = ''
                #   pytest -vv
                # '';
                patchPhase = "";
                #preCheck = "";

                doCheck = false;
                doInstallCheck = false;

                buildInputs = old.buildInputs or [];
                nativeBuildInputs = old.nativeBuildInputs or [];
                format = old.format or "pyproject";
                pythonImportsCheck = old.pythonImportsCheck or [];
            });

        };
        };
        };

    pkgs = import nixpkgs { 
      inherit system;
      overlays = [ overlay ];  
    };
  in
  {
    packages.${system}.default = 
        pkgs.python311Packages.buildPythonApplication {
            pname = "listentui";
            version = "1.2.1";
            src = ./.;

            format = "pyproject";
            nativeBuildInputs = [ pkgs.python311Packages.poetry-core ];

            propagatedBuildInputs = with pkgs.python311Packages; [
                aiohttp
                gql
                markdownify
                pip
                psutil
                pypresence
                mpv
                readchar
                rich
                tomli
                tomli-w
                requests_toolbelt
                websockets
                yt-dlp
                ytmusicapi
            ];
        };

        postFixup = ''
          wrapPythonProgram "$out/bin/listentui" \
          --prefix LD_LIBRARY_PATH: "${pkgs.mpv}.lib"
        '';
        

        devShell.${system} = pkgs.mkShell {
          buildInputs = [
            self.packages.${system}.default
            pkgs.mpv
          ];
        };
  };
}