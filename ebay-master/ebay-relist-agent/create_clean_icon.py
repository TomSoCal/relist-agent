#!/usr/bin/env python3
from PIL import Image, ImageDraw
import math

# Create a new image with transparent background
size = 256
image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
draw = ImageDraw.Draw(image)

# Load the original icon to get the colorful parts
original = Image.open(r"C:\Users\tom\Downloads\ERA_Info.png").convert("RGBA")

# Resize original to our size
original_resized = original.resize((size, size), Image.Resampling.LANCZOS)

# Copy pixels, but only within a circular mask
center_x, center_y = size // 2, size // 2
radius = size // 2 - 5

result = Image.new('RGBA', (size, size), (0, 0, 0, 0))
pixels_orig = original_resized.load()
pixels_result = result.load()

for y in range(size):
    for x in range(size):
        # Calculate distance from center
        dist = math.sqrt((x - center_x)**2 + (y - center_y)**2)

        # Only keep pixels within the circle
        if dist <= radius:
            r, g, b, a = pixels_orig[x, y]

            # Skip pure blue and very dark pixels
            is_blue = (b > r + 40 and b > g + 40)
            is_very_dark = (r < 30 and g < 30 and b < 30)

            if not (is_blue or is_very_dark):
                pixels_result[x, y] = (r, g, b, a)

result.save(r"C:\Users\tom\agents\ebay-master\ebay-relist-agent\INFO_ICON.png", "PNG")
print("Clean icon created!")
