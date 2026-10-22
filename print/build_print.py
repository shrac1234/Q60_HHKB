#!/usr/bin/env python3
"""Build the printable guide HTML from the README SVGs (light palette only).

  python3 print/build_print.py      -> print/q60-hhkb-print.html
"""
import os, re

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "..", "assets")


def light_svg(name):
    """Inline an asset SVG with its light-theme CSS variables resolved."""
    svg = open(os.path.join(ASSETS, name)).read()
    style = re.search(r"<style>(.*?)</style>", svg, re.S).group(1)
    light = re.match(r"svg\{([^}]*)\}", style).group(1)
    palette = dict(p.split(":", 1) for p in light.split(";"))
    rules = re.sub(r"^svg\{[^}]*\}@media[^{]*\{svg\{[^}]*\}\}", "", style)
    resolve = lambda s: re.sub(r"var\(--([a-z0-9]+)\)", lambda m: palette["--" + m.group(1)], s)
    svg = svg.replace(f"<style>{style}</style>", f"<style>{resolve(rules)}</style>")
    svg = resolve(svg)
    return re.sub(r' width="[^"]*" height="[^"]*"', "", svg, count=1)


TEMPLATE = open(os.path.join(HERE, "template.html")).read()
html = (TEMPLATE
        .replace("{{WORDMARK}}", light_svg("wordmark.svg"))
        .replace("{{FN_BOARD}}", light_svg("fn-layer.svg"))
        .replace("{{LIGHT_BOARD}}", light_svg("lighting-layer.svg")))
out = os.path.join(HERE, "q60-hhkb-print.html")
open(out, "w").write(html)
print("wrote", out)
