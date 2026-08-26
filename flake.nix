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
      # The deployable site: rendered by Hugo from Org content.
      packages = forAllSystems (pkgs: {
        default = pkgs.stdenvNoCC.mkDerivation {
          pname = "contour-website";
          version = "0.1.0";

          src = pkgs.lib.fileset.toSource {
            root = ./.;
            fileset = pkgs.lib.fileset.unions [
              ./hugo.toml
              ./content
              ./layouts
              ./style.css
              ./robots.txt
              ./llms.txt
              ./CNAME
              ./img
            ];
          };

          dontConfigure = true;
          nativeBuildInputs = [ pkgs.hugo ];

          buildPhase = ''
            runHook preBuild
            export HUGO_ENVIRONMENT=production
            export HUGO_ENV=production
            hugo --minify --destination public
            touch public/.nojekyll
            runHook postBuild
          '';

          doCheck = true;
          checkPhase = ''
            runHook preCheck
            expected="
            public/index.html
            public/about/index.html
            public/product/index.html
            public/product/model-context-layer/index.html
            public/product/failure-propagation/index.html
            public/product/reliability-engineering/index.html
            public/product/sensor-intelligence/index.html
            public/use-cases/index.html
            public/blog/index.html
            public/contact/index.html
            public/CNAME
            public/.nojekyll
            "
            for f in $expected; do
              test -f "$f" || { echo "missing generated route or Pages file: $f" >&2; exit 1; }
            done
            if grep -R '{{[<%]' public; then
              echo "unresolved Hugo shortcode leaked into public output" >&2
              exit 1
            fi
            runHook postCheck
          '';

          installPhase = ''
            runHook preInstall
            mkdir -p "$out"
            cp -r public/. "$out"/
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

          liveServer = pkgs.writeShellApplication {
            name = "contour-serve";
            runtimeInputs = [ pkgs.hugo ];
            text = ''
              port="''${1:-1313}"
              echo "Contour → http://localhost:$port  (Hugo source: $PWD)"
              exec hugo server --bind 127.0.0.1 --baseURL "http://localhost:$port/" --port "$port"
            '';
          };
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
              exec ./diagrams/render.sh "$@"
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
          packages = [ pkgs.caddy pkgs.hugo pkgs.libxml2 pkgs.plantuml pkgs.graphviz ];
        };
      });
    };
}
