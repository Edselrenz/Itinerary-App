import zipfile
from PIL import Image
import os

os.makedirs('scratch/fig_images', exist_ok=True)

with zipfile.ZipFile('Travel Itinerary App.fig', 'r') as z:
    for f in z.namelist():
        if f.startswith('images/') and len(f) > 10:
            dest = os.path.join('scratch/fig_images', os.path.basename(f) + '.png')
            with open(dest, 'wb') as out:
                out.write(z.read(f))

print("Extracted all images to scratch/fig_images")
# Let's see if any image contains the hiker by comparing to user_hiker_crop
import glob
import numpy as np

user_img = Image.open("scratch/user_hiker_crop.jpg").convert('RGB')
user_arr = np.array(user_img.resize((100, 100)), dtype=float)

diffs = []
for p in glob.glob('scratch/fig_images/*.png'):
    im = Image.open(p).convert('RGB')
    arr = np.array(im.resize((100, 100)), dtype=float)
    diff = np.mean(np.abs(arr - user_arr))
    diffs.append((diff, p, im.size))

diffs.sort()
print("Top 5 matches in fig_images:")
for d, p, sz in diffs[:5]:
    print(d, p, sz)

