"""Render the two object traces summarized in the excavation dossiers."""
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, indent, tostring

HERE = Path(__file__).resolve().parent
CHAINS = [
    ("Eynan / ʿAin Mallaha", [
        ("Field record", ["The 1955 photo shows", "Shelter 1 and its rim."], "#e1eee8"),
        ("Laboratory record", ["Sample 86-1 came through", "the Hebrew University collection."], "#e1eee8"),
        ("Unresolved identity", ["The descriptions fit. No shared", "field number has been traced."], "#f8e9ce"),
    ]),
    ("Kfar Samir", [
        ("Field record", ["The winter 1994 excavation", "recovered three braided pieces."], "#e1eee8"),
        ("Object identified", ["Matching photographs trace the", "pieces to catalogue item KS 2."], "#e1eee8"),
        ("Unresolved use", ["The braiding was directly dated.", "Use for pressing remains open."], "#f8e9ce"),
    ]),
]


def draw():
    svg = Element("svg", xmlns="http://www.w3.org/2000/svg", width="960", height="354",
                  viewBox="0 0 960 354", role="img", attrib={"aria-labelledby": "title desc"})
    SubElement(svg, "title", id="title").text = "What the excavation records identify"
    SubElement(svg, "desc", id="desc").text = (
        "Shelter 1 and Eynan sample 86-1 lack a shared inventory number. At Kfar Samir, "
        "the same field photograph identifies the dated basket, while its use remains open.")
    SubElement(svg, "rect", width="960", height="354", fill="#fbfaf6")

    def label(x, y, value, size, bold=False):
        node = SubElement(svg, "text", x=str(x), y=str(y), fill="#213a36",
                          attrib={"font-family": "DejaVu Sans, sans-serif", "font-size": str(size),
                                  "font-weight": "600" if bold else "400"})
        node.text = value

    label(23, 35, "What the excavation records identify", 25, True)
    for row, (name, stages) in enumerate(CHAINS):
        top = 83 + 143 * row
        label(23, top - 12, name, 18, True)
        for i, (heading, lines, color) in enumerate(stages):
            x = 23 + 311 * i
            SubElement(svg, "rect", x=str(x), y=str(top), width="294", height="90", rx="5", fill=color)
            label(x + 12, top + 25, heading, 16, True)
            for j, line in enumerate(lines):
                label(x + 12, top + 50 + 21 * j, line, 15)
    indent(svg)
    return tostring(svg, encoding="unicode") + "\n"


if __name__ == "__main__":
    (HERE / "object-traces.svg").write_text(draw(), encoding="utf-8")
