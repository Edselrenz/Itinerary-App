from PIL import Image

img_path = r"C:/Users/Edward/.gemini/antigravity/brain/227d42fc-f285-416b-839a-2864eb1a7ab1/.user_uploaded/media_1793332685774_b6884c9f.jpg"
im = Image.open(img_path)
print("Image size:", im.size)

# Sample some colors
# Let's sample the blue button color (around center-ish vertically, width center)
# The image size is likely around 300-800px wide
w, h = im.size

# Find the blue button color by scanning down the center column
blue_colors = []
for y in range(int(h * 0.3), int(h * 0.65), 5):
    pixel = im.getpixel((w // 2, y))
    if pixel[2] > 200 and pixel[0] < 100:  # strong blue
        blue_colors.append((y, pixel))

if blue_colors:
    print(f"Sampled {len(blue_colors)} blue pixels. Example:", blue_colors[0])
    hex_col = "#{:02x}{:02x}{:02x}".format(blue_colors[0][1][0], blue_colors[0][1][1], blue_colors[0][1][2])
    print("Hex button color:", hex_col)

