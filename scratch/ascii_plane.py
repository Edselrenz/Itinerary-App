import re
from PIL import Image

# Let's check plane_crop.png non-white pixels
im = Image.open(r"scratch/plane_crop.png")
w, h = im.size
print("Plane crop size:", w, h)
for y in range(0, h, 4):
    line = ""
    for x in range(0, w, 2):
        r, g, b = im.getpixel((x, y))[:3]
        if r < 200 and g < 200 and b > 150:
            line += "#"
        else:
            line += "."
    if "#" in line:
        print(line)

