import glob
from PIL import Image

files = glob.glob("Project/src/assets/images/[0-9a-f]*.png") + glob.glob("Project/src/assets/images/[0-9a-f]*.jpg")

# Let's inspect the dimensions and print info for each
for f in sorted(files):
    im = Image.open(f)
    print(f"{f}: size={im.size}, mode={im.mode}")

