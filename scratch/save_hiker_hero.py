from PIL import Image
import numpy as np

im = Image.open(r"C:/Users/Edward/.gemini/antigravity/brain/227d42fc-f285-416b-839a-2864eb1a7ab1/.user_uploaded/media_1793336850023_e7049ff9.jpg")
arr = np.array(im)
w, h = im.size

# In row y=200, find left edge where background black ends and phone screen begins
# The phone outer bezel is purple, screen is photo
for x in range(0, 100):
    if arr[200, x, 0] > 30 and arr[200, x, 1] > 30:
        print("Left screen begins around x =", x)
        break

for x in range(w-1, w-100, -1):
    if arr[200, x, 0] > 30 and arr[200, x, 1] > 30:
        print("Right screen ends around x =", x)
        break

for y in range(0, 100):
    if arr[y, w//2, 0] > 30 and arr[y, w//2, 1] > 30:
        print("Top screen begins around y =", y)
        break

# The hiker image itself:
# Let's crop from top of hiker to y=375
# Notice top of hiker in the screenshot has sky and trees
# Let's crop from y=30 to y=375, x=39 to x=356
hiker_full = im.crop((39, 28, 356, 375))
hiker_full.save("Project/src/assets/images/guest_hiker_hero.png")
print("Saved guest_hiker_hero.png with size:", hiker_full.size)

