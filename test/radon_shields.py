# coding: utf-8

import os.path
import re
import sys


if len(sys.argv) != 4:
    print(f"usage: {os.path.basename(__file__)} CLASS_LETTER integer_number color", file=sys.stderr)
    sys.exit(1)


class_letter_pattern = r"[A-Z]"
if not re.fullmatch(class_letter_pattern, sys.argv[1]):
    print(f"CLASS_LETTER must match {class_letter_pattern}", file=sys.stderr)
    sys.exit(2)

number_pattern = r"[0-9]+"
if not re.fullmatch(number_pattern, sys.argv[2]):
    print(f"integer_number must match {number_pattern}", file=sys.stderr)
    sys.exit(3)


colors = {"green": "#97ca00", "yellow": "#dfb317", "orange": "#fe7d37", "red": "#e05d44"}

if sys.argv[3].lower() not in colors:
    print(f"color must be in {colors.keys()}", file=sys.stderr)
    sys.exit(4)


class_letter = sys.argv[1]
number = sys.argv[2]
color = colors[sys.argv[3].lower()]

right_margin = 60
char_width = 70
middle_gap_width = 80
class_letter_center = 95

left_field_width_in_pixels = 17

text_length = len(number) * char_width
text_left_offset = int(class_letter_center + char_width / 2 + middle_gap_width)
image_width_in_pixels = int((text_left_offset + text_length + right_margin) / 10)
text_center = int(text_left_offset + text_length / 2)


svg = f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{image_width_in_pixels}" height="20" role="img" aria-label="{class_letter}: {number}">

<title>{class_letter}: {number}</title>

<linearGradient id="s" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
</linearGradient>

<clipPath id="r">
    <rect width="{image_width_in_pixels}" height="20" rx="3" fill="#fff"/>
</clipPath>

<g clip-path="url(#r)">
    <rect width="17" height="20" fill="#555"/>
    <rect x="{left_field_width_in_pixels}" width="{image_width_in_pixels - left_field_width_in_pixels}" height="20" fill="{color}"/>
    <rect width="{image_width_in_pixels}" height="20" fill="url(#s)"/>
</g>

<g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" text-rendering="geometricPrecision" font-size="110">
    <text aria-hidden="true" x="{class_letter_center}" y="150" fill="#010101" fill-opacity=".3" transform="scale(.1)" textLength="{char_width}">{class_letter}</text>
    <text x="{class_letter_center}" y="140" transform="scale(.1)" fill="#fff" textLength="{char_width}">{class_letter}</text>
    <text aria-hidden="true" x="{text_center}" y="150" fill="#010101" fill-opacity=".3" transform="scale(.1)" textLength="{text_length}">{number}</text>
    <text x="{text_center}" y="140" transform="scale(.1)" fill="#fff" textLength="{text_length}">{number}</text>
</g>

</svg>"""

print(svg)
