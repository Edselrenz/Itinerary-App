# Let's inspect the airplane icon in header_crop.png
from PIL import Image

im = Image.open(r"scratch/header_crop.png")
# The airplane is on the left of "Trip mo, trip ko"
# Let's crop just the airplane
plane_crop = im.crop((10, 10, 80, 80))
plane_crop.save(r"scratch/plane_crop.png")
print("Saved plane crop")

