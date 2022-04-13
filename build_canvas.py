#!/usr/bin/env python3

import sys
from PIL import Image

import trplace

if __name__ == "__main__":
    assert len(
        sys.argv) > 1, f"Usage: {sys.argv[0]} output.png [starting_canvas.png] < input.trp"
    canvas = trplace.Canvas()
    if len(sys.argv) > 2:
        canvas.from_image(Image.open(sys.argv[2]))

    reader = trplace.Reader(sys.stdin.buffer)
    for ts, _, color, x, y in reader:
        canvas.apply_pixel(ts, x, y, color)

    canvas.to_image().save(sys.argv[1])
