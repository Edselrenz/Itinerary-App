import glob
from PIL import Image

# Let's inspect all 44 images in Project/src/assets/images
files = glob.glob("Project/src/assets/images/[0-9a-f]*.png") + glob.glob("Project/src/assets/images/[0-9a-f]*.jpg")
print(f"Total raw hash images: {len(files)}")

# The hiker is a girl with maroon shirt, mountains behind her.
# Let's check dominant colors or inspect
for f in files:
    im = Image.open(f)
    w, h = im.size
    # let's sample the top center (sky/mountains) and center (maroon shirt)
    # top center: sky or mountains (green/blue/brown)
    # middle center: maroon shirt (r > 80, g < 40, b < 40)
    top_p = im.getpixel((w//2, h//5))
    mid_p = im.getpixel((w//2, h//2))
    # print file if mid_p is reddish/maroon or if it's large
    if isinstance(mid_p, tuple) and len(mid_p) >= 3:
        r, g, b = mid_p[:3]
        if r > 70 and g < 60 and b < 60:
            print(f"MATCH (maroon shirt): {f} size: {w}x{h}, mid: {mid_p}, top: {top_p}")

