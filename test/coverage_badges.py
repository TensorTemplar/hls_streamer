import argparse
import xml.etree.ElementTree as ET
from typing import Literal


def parse_coverage_xml(file_path: str) -> float:
    tree = ET.parse(file_path)
    root = tree.getroot()
    coverage = float(root.attrib["line-rate"]) * 100
    return coverage


def determine_badge_color(coverage: float) -> Literal["#4c1", "#dfb317", "#e05d44"]:
    if coverage >= 80:
        return "#4c1"  # Green
    elif coverage >= 60:
        return "#dfb317"  # Yellow
    else:
        return "#e05d44"  # Red


def create_coverage_badge(coverage: float, color: str, output_path: str) -> None:
    coverage_text = f"{coverage:.2f}%"
    left_field_text = "Coverage"
    font_size = 12  # Font size in pixels

    # Calculate text lengths in pixels
    left_text_length_pixels = len(left_field_text) * font_size
    right_text_length_pixels = len(coverage_text) * font_size

    # Calculate the width of each field
    left_field_width = left_text_length_pixels * 1.2
    right_field_width = right_text_length_pixels * 1.2
    image_width = left_field_width + right_field_width

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{image_width}" height="20" role="img" aria-label="Coverage: {coverage_text}">
    <title>Coverage: {coverage_text}</title>
    <linearGradient id="s" x2="0" y2="100%">
        <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
        <stop offset="1" stop-opacity=".1"/>
    </linearGradient>
    <clipPath id="r">
        <rect width="{image_width}" height="20" rx="3" fill="#fff"/>
    </clipPath>
    <g clip-path="url(#r)">
        <rect width="{left_field_width}" height="20" fill="#555"/>
        <rect x="{left_field_width}" width="{right_field_width}" height="20" fill="{color}"/>
        <rect width="{image_width}" height="20" fill="url(#s)"/>
    </g>
    <g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" font-size="{font_size}">
        <text x="{left_field_width / 2}" y="15">{left_field_text}</text>
        <text x="{left_field_width + right_field_width / 2}" y="15">{coverage_text}</text>
    </g>
    </svg>
    """

    with open(output_path, "w") as file:
        file.write(svg)



def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a coverage badge from a coverage XML file.")
    parser.add_argument("coverage_file", type=str, help="Path to the coverage XML file")
    parser.add_argument("output_file", type=str, help="Path to output the coverage badge SVG file")
    args = parser.parse_args()

    coverage = parse_coverage_xml(args.coverage_file)
    color = determine_badge_color(coverage)
    create_coverage_badge(coverage, color, args.output_file)


if __name__ == "__main__":
    main()
