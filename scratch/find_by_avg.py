import glob
from PIL import Image
import numpy as np

files = glob.glob("Project/src/assets/images/[0-9a-f]*.*")
user_img = Image.open("scratch/user_hiker_crop.jpg").convert('RGB')
user_avg = np.mean(np.array(user_img), axis=(0,1))

diffs = []
for f in files:
    im = Image.open(f).convert('RGB')
    avg = np.mean(np.array(im), axis=(0,1))
    d = np.linalg.norm(avg - user_avg)
    diffs.append((d, f, im.size, avg))

diffs.sort()
print("Top 10 closest average RGB:")
for d, f, sz, avg in diffs[:10]:
    print(f"dist={d:.2f} -> {f} {sz} {avg.astype(int)}")

