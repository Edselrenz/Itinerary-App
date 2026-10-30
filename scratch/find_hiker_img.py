import os
import glob
from PIL import Image

image_files = glob.glob("Project/src/assets/images/*.*")
print(f"Checking {len(image_files)} image files...")

# Let's inspect the dimensions of the images to find candidates
candidates = []
for f in image_files:
    try:
        im = Image.open(f)
        w, h = im.size
        # The hiker photo is portrait or square, relatively large
        candidates.append((f, w, h))
    except Exception as e:
        pass

# Let's inspect image from user upload to compare
user_img = Image.open(r"C:/Users/Edward/.gemini/antigravity/brain/227d42fc-f285-416b-839a-2864eb1a7ab1/.user_uploaded/media_1793336850023_e7049ff9.jpg")
print("User image size:", user_img.size)

# Crop the hiker from user image (roughly y=30 to y=380, x=40 to x=365)
hiker_crop = user_img.crop((40, 40, 365, 380))
hiker_crop.save("scratch/user_hiker_crop.jpg")
print("Saved user hiker crop")

