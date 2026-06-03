#!/usr/bin/env python3
from PIL import Image, ImageDraw, ImageFont
import os

# Create a 256x256 image with transparent background
size = 256
image = Image.new('RGBA', (size, size), (255, 255, 255, 0))
draw = ImageDraw.Draw(image)

# Colors
WHITE = (255, 255, 255, 255)
BLUE = (0, 102, 255, 255)  # #0066FF from design system

# Draw solid blue circle background
radius = size // 2
draw.ellipse([0, 0, size, size], fill=BLUE, outline=BLUE)

# Draw white "i" character
try:
    # Try to use a bold sans-serif font
    font = ImageFont.truetype("arial.ttf", 140)
except:
    try:
        font = ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", 140)
    except:
        # Fallback to default font
        font = ImageFont.load_default()

# Draw the "i" character centered
text = "i"
bbox = draw.textbbox((0, 0), text, font=font)
text_width = bbox[2] - bbox[0]
text_height = bbox[3] - bbox[1]
x = (size - text_width) // 2
y = (size - text_height) // 2 - 8

draw.text((x, y), text, fill=WHITE, font=font)

# Save as PNG
output_path = os.path.join(os.path.dirname(__file__), "INFO_ICON.png")
image.save(output_path, "PNG")
print(f"Info icon created: {output_path}")
