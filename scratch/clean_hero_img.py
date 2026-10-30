from PIL import Image
import numpy as np

im = Image.open(r"C:/Users/Edward/.gemini/antigravity/brain/227d42fc-f285-416b-839a-2864eb1a7ab1/.user_uploaded/media_1793336850023_e7049ff9.jpg")
# Crop screen area from top of screen to y=375
# Left: 36, Right: 360, Top: 25, Bottom: 375
screen_img = im.crop((36, 25, 360, 375))
arr = np.array(screen_img)

# Back arrow is around x: 18-35, y: 70-85 inside screen_img
# Let's inspect coordinates of back arrow in screen_img
arrow_crop = screen_img.crop((15, 65, 45, 95))
arrow_crop.save("scratch/arrow_crop.png")

# Also let's patch the arrow area using the mountain pixels immediately to the right and above
# Mountain area around x=48..65, y=65..95 has same vegetation pattern
patch = arr[65:95, 45:75]
# Blend patch slightly or copy
cleaned_arr = arr.copy()
# Smoothly blend the patch over x=15..45, y=65..95
cleaned_arr[65:95, 15:45] = patch

# Also over the dynamic island at top center (x=120..205, y=10..38):
# We can patch with sky pixels from left (x=70..110) or right (x=215..255)
sky_patch = arr[5:38, 70:155]
# In mobile web or Ionic app, the status bar sits on top of this.
# But having clean sky is great!
res_img = Image.fromarray(cleaned_arr)
res_img.save("Project/src/assets/images/guest_hiker_hero.png")
print("Saved cleaned guest_hiker_hero.png (size:", res_img.size, ")")

