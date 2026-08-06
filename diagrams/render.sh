#!/usr/bin/env bash
# Render diagrams/*.puml into ../img/*.svg, rewrite the design tokens from literal
# hexes into var(--token), then inline each SVG into the pages that ask for it.
#
#   nix run .#diagrams      — regenerate and re-inject everything
#
# A page asks for a diagram with a marker pair, and this script owns whatever
# sits between them:
#
#   <figure>
#     <!-- @diagram asset-graph -->
#     <!-- /@diagram -->
#     <figcaption>...</figcaption>
#   </figure>
#
# Diagrams are inlined rather than linked because the whole site themes by token
# swap: an <img> cannot see the page's prefers-color-scheme, so a linked SVG
# would stay in light mode on a dark page. Inlining also keeps the label text as
# real text — selectable, and visible to anything reading the page.
#
# The generated SVGs are committed, so the site stays a pile of static files with
# no build step in the deploy path.
#
#   --skip-puml   do everything except re-render the .puml diagrams
#
# PlantUML sizes its boxes from the JVM's font metrics, and the JVM resolves
# fonts differently per platform: macOS has Helvetica, a Linux CI runner does
# not and silently substitutes something wider. The same source therefore gives
# a 858px sequence diagram here and a 963px one on ubuntu-latest. So the .puml
# render is reproducible per machine but not across machines, and CI must not
# re-run it — it would rewrite every diagram and call the committed ones stale.
#
# Everything else is deterministic and worth verifying: mark.py is pure geometry
# with no font involved, the hand-authored SVGs are copied byte for byte, and
# injection is text substitution. --skip-puml runs exactly that set, so CI can
# require a clean tree afterwards and still catch the realistic mistake — an
# asset regenerated but never inlined, or generated HTML edited by hand.
set -euo pipefail
cd "$(dirname "$0")"

render_puml=1
for arg in "$@"; do
  case "$arg" in
    --skip-puml) render_puml=0 ;;
    *) echo "unknown argument: $arg" >&2; exit 2 ;;
  esac
done

root="$(cd .. && pwd)"
out="$root/img"
mkdir -p "$out"

echo "generating:"
python3 mark.py

[ "$render_puml" = 1 ] && echo "rendering:" || echo "rendering: skipped (--skip-puml)"
for src in *.puml; do
  [ "$render_puml" = 1 ] || break
  [ "$src" = theme.puml ] && continue
  name="${src%.puml}"
  svg="$out/$name.svg"

  plantuml -tsvg -nometadata -o "$out" "$src"

  perl -0pi -e '
    # design tokens -> custom properties (see theme.puml)
    s/#F4F2ED/var(--paper)/gi;
    s/#EDEAE3/var(--panel)/gi;
    s/#14110F/var(--ink)/gi;
    s/#6B655E/var(--muted)/gi;
    s/#DAD5CC/var(--rule)/gi;
    s/#1E40AF/var(--accent)/gi;
    # plain black only ever turns up on transparent hit-area rects, but map it so
    # a future diagram cannot smuggle a hardcoded colour past the theme
    s/#000000/var(--ink)/gi;

    # let CSS own the type: style.css sets the site font stack on figure svg text
    s/\sfont-family="[^"]*"//g;
    s/font-family:[^;"]*;?//g;

    # Drop the fixed pixel box, and drop preserveAspectRatio="none" with it —
    # left in, it stretches the diagram to whatever box CSS gives it. The
    # viewBox alone carries the geometry.
    1 while s/(<svg[^>]*?)\s(?:width|height)="[^"]*"/$1/;
    s/(<svg[^>]*?)\spreserveAspectRatio="[^"]*"/$1/;
    s/(<svg[^>]*?)\sstyle="[^"]*"/$1/;
  ' "$svg"

  # Cap the figure at the diagram's natural width. Without this, width:100% in a
  # wider column magnifies the label text along with the geometry — PlantUML's
  # own 13px is already the right size next to 16px body copy.
  natural="$(perl -ne 'if (/viewBox="0 0 ([\d.]+)/) { print int($1 + 0.5); last }' "$svg")"
  perl -0pi -e "s/(<svg\b)/\$1 style=\"max-width:${natural}px\"/" "$svg"

  printf "  %-20s %4spx wide  %6s bytes\n" "$name.svg" "$natural" "$(wc -c <"$svg" | tr -d ' ')"
done

# Hand-authored figures — anything PlantUML cannot draw, charts above all. They
# already reference var(--token) directly, so they are copied through untouched
# and picked up by the same injection pass.
for hand in *.svg; do
  [ -e "$hand" ] || continue
  # drop the authoring comment: it documents the source, it should not ship
  perl -0pe 's/\A\s*(?:<!--.*?-->\s*)+//s' "$hand" >"$out/$hand"
  printf "  %-20s %4s     hand-authored\n" "$hand" "$(perl -ne 'if (/viewBox="0 0 ([\d.]+)/) { print int($1 + 0.5); last }' "$hand")px"
done

echo "injecting:"
while IFS= read -r page; do
  before="$(wc -c <"$page" | tr -d ' ')"
  perl -0pi -e '
    sub raw {
      my $p = shift;
      open my $fh, "<", "'"$out"'/$p" or die "missing generated asset: $p\n";
      local $/; my $s = <$fh>; close $fh;
      $s =~ s/^\s+|\s+$//g;
      return $s;
    }
    sub svg { return raw($_[0] . ".svg"); }
    s{(<!--\s*\@diagram\s+(\S+)\s*-->)(.*?)(<!--\s*/\@diagram\s*-->)}
     {$1 . "\n" . svg($2) . "\n      " . $4}gse;
    # the favicon is the same mark, so one generator owns every instance of it
    s{(<!--\s*\@favicon\s*-->)(.*?)(<!--\s*/\@favicon\s*-->)}
     {$1 . "\n" . raw("favicon.html") . "\n" . $3}gse;
  ' "$page"
  printf "  %-46s %6s -> %6s bytes\n" "${page#$root/}" "$before" "$(wc -c <"$page" | tr -d ' ')"
done < <(grep -rlE '@diagram|@favicon' "$root" --include='*.html' | sort)
