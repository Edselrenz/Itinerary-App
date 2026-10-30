import glob
from PIL import Image
import numpy as np

user_crop = Image.open("scratch/user_hiker_crop.jpg").convert('RGB').resize((64, 64))
user_arr = np.array(user_crop, dtype=float)

best_diff = float('inf')
best_file = None

results = []
for f in glob.glob("Project/src/assets/images/*.*"):
    try:
        im = Image.open(f).convert('RGB').resize((64, 64))
        arr = np.array(im, dtype=float)
        diff = np.mean(np.abs(arr - user_arr))
        results.append((diff, f))
    except Exception:
        pass

results.sort()
print("Top 5 matches:")
for diff, f in results[:5]:
    print(f"Diff: {diff:.2f} -> {f}")

