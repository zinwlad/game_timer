from PIL import Image, ImageDraw, ImageFont
import os

# Create a new image with a white background
size = (256, 256)
image = Image.new('RGBA', size, (255, 255, 255, 0))
draw = ImageDraw.Draw(image)

# Draw a blue circle
circle_bbox = (20, 20, 236, 236)
draw.ellipse(circle_bbox, fill=(65, 105, 225, 255))  # Royal Blue

# Draw clock hands
center = (128, 128)
# Hour hand
draw.line((center[0], center[1], center[0], center[1]-60), fill=(255, 255, 255), width=8)
# Minute hand
draw.line((center[0], center[1], center[0]+40, center[1]), fill=(255, 255, 255), width=6)

# Draw small circle in center
draw.ellipse((123, 123, 133, 133), fill=(255, 255, 255))

# Save as ICO
image.save('timer.ico', format='ICO', sizes=[(256, 256)])
