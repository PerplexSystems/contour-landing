{
  description = "Contour — static marketing site";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }:
    let
      systems = [ "aarch64-darwin" "x86_64-darwin" "aarch64-linux" "x86_64-linux" ];
      forAllSystems = f:
        nixpkgs.lib.genAttrs systems (system: f nixpkgs.legacyPackages.${system});
    in
    {
      # The deployable site: exactly the files that should ship, nothing else.
      packages = forAllSystems (pkgs: {
        default = pkgs.stdenvNoCC.mkDerivation {
          pname = "contour-website";
          version = "0.1.0";

          src = pkgs.lib.fileset.toSource {
            root = ./.;
            fileset = pkgs.lib.fileset.unions [
              ./index.html
              ./style.css
              ./robots.txt
              ./sitemap.xml
              ./llms.txt
              ./about
              ./product
              ./use-cases
              ./contact
            ];
          };

          dontConfigure = true;
          dontBuild = true;

          installPhase = ''
            runHook preInstall
            mkdir -p "$out"
            cp -r ./. "$out"/
            runHook postInstall
          '';
        };
      });

      apps = forAllSystems (pkgs:
        let
          # $1 = port (default 8080), $2 = root to serve
          server = name: root: pkgs.writeShellApplication {
            inherit name;
            runtimeInputs = [ pkgs.caddy ];
            text = ''
              port="''${1:-8080}"
              root=${root}
              echo "Contour → http://localhost:$port  (root: $root)"
              exec caddy file-server --root "$root" --listen ":$port"
            '';
          };

          liveServer = server "contour-serve" ''"$PWD"'';
          builtServer = server "contour-preview" "${self.packages.${pkgs.system}.default}";
        in
        {
          # nix run          — serve the working tree, so edits show on refresh
          default = {
            type = "app";
            program = "${liveServer}/bin/contour-serve";
          };

          # nix run .#preview — serve the built derivation, exactly what deploys
          preview = {
            type = "app";
            program = "${builtServer}/bin/contour-preview";
          };
        });

      devShells = forAllSystems (pkgs: {
        default = pkgs.mkShell {
          packages = [ pkgs.caddy pkgs.libxml2 ];
        };
      });
    };
}
