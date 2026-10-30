import glob
from PIL import Image
import numpy as np

user_img = Image.open("scratch/user_hiker_crop.jpg").convert('RGB')
uw, uh = user_img.size

candidates = [
    'Project/src/assets/images/e20a1f159a6c0d5007a1cff0c0b7746fceb10364.png',
    'Project/src/assets/images/7c93d7c36861a617e298e1137c2dc6a29a5f021b.png',
    'Project/src/assets/images/e57cb14a8560ce343df12846535d619ace8adf2e.png',
    'Project/src/assets/images/0a6c36e4de50eaf3ccc7b9a5282265163ad94604.png',
    'Project/src/assets/images/54d2311ab12f0f44cdc4a92c8faabb6c6ca034fb.png'
]

for c in candidates:
    im = Image.open(c).convert('RGB')
    print(c, im.size)
    # in the phone frame, the top half is this image. Let's crop top half of im or check
    # Let's see average colors
    avg = np.mean(np.array(im), axis=(0,1))
    print("  avg RGB:", avg)

user_avg = np.mean(np.array(user_img), axis=(0,1))
print("User hiker crop avg RGB:", user_avg)

