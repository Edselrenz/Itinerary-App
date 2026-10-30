from PIL import Image

im = Image.open("Project/src/assets/images/ce447c0e3b1306e2ff9defbc9ab1a2cd7aa79495.png")
print("ce44 size:", im.size)
# Let's save a crop of ce44 to scratch to compare
im.save("scratch/ce44.jpg")

# Also let's check user_hiker_crop
user_crop = Image.open("scratch/user_hiker_crop.jpg")
print("user crop size:", user_crop.size)

# Let's check similarity
im_res = im.resize(user_crop.size)
import numpy as np
diff = np.mean(np.abs(np.array(im_res.convert('RGB'), dtype=float) - np.array(user_crop, dtype=float)))
print("Direct pixel diff with ce44:", diff)

