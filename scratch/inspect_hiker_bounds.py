from PIL import Image

im = Image.open(r"C:/Users/Edward/.gemini/antigravity/brain/227d42fc-f285-416b-839a-2864eb1a7ab1/.user_uploaded/media_1793336850023_e7049ff9.jpg")
w, h = im.size
print("User image dimensions:", w, h)

# Let's crop from inside the phone bezel
# The phone frame in the screenshot has bezel around it
# Let's find the inner screen boundaries
# The notch (dynamic island) is around x=w/2, y=55
# The screen left is around x=39, screen right around x=357
# The screen top is around y=30, screen bottom around y=715
# The hiker image starts at top of screen and ends at y=375 where the white card begins
# Let's find exact pixel coordinates
import numpy as np

arr = np.array(im)
# Find where the white card starts below the hiker
# Column w//2, scanning down from y=300 to y=420
for y in range(300, 420):
    p = arr[y, w//2]
    # check if pure white (255, 255, 255)
    if p[0] > 250 and p[1] > 250 and p[2] > 250:
        print(f"White starts at y={y}")
        break

