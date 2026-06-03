#!/usr/bin/env python3
from PIL import Image
import os

# Load the original icon
input_path = r"C:\Users\tom\Downloads\ERA_Info.png"
img = Image.open(input_path).convert("RGBA")

# Get image dimensions
width, height = img.size

# Create a new image with transparent background
result = Image.new("RGBA", img.size, (0, 0, 0, 0))

# Copy only the non-blue parts
pixels = img.load()
result_pixels = result.load()

for y in range(height):
    for x in range(width):
        r, g, b, a = pixels[x, y]

        # Keep pixels that are NOT the blue background
        # Remove anything that is primarily blue (high B, low R, low G)
        is_blue_bg = (b > 150 and r < 150 and g < 180)

        # Also remove very dark near-black corners (transparency areas)
        is_dark_transparent = (r < 50 and g < 50 and b < 50 and a < 50)

        if not (is_blue_bg or is_dark_transparent):
            result_pixels[x, y] = (r, g, b, a)

# Save with transparent background
output_path = os.path.join(os.path.dirname(__file__), "INFO_ICON.png")
result.save(output_path, "PNG")
print(f"Icon with transparent background saved: {output_path}")
