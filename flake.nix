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

          # Renders diagrams/*.puml and re-inlines them into the pages. Writes into
          # the working tree, not the store, so it has to run from the repo root —
          # the generated SVGs are committed and the deploy stays copy-only.
          diagrams = pkgs.writeShellApplication {
            name = "contour-diagrams";
            runtimeInputs = [ pkgs.plantuml pkgs.graphviz pkgs.perl pkgs.python3 ];
            text = ''
              if [ ! -x ./diagrams/render.sh ]; then
                echo "run this from the repo root (no ./diagrams/render.sh here)" >&2
                exit 1
              fi
              exec ./diagrams/render.sh
            '';
          };
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

          # nix run .#diagrams — re-render the figures after editing a .puml
          diagrams = {
            type = "app";
            program = "${diagrams}/bin/contour-diagrams";
          };
        });

      devShells = forAllSystems (pkgs: {
        default = pkgs.mkShell {
          packages = [ pkgs.caddy pkgs.libxml2 pkgs.plantuml pkgs.graphviz ];
        };
      });
    };
}
