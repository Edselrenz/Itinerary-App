from PIL import Image

for f in [
    'Project/src/assets/images/e20a1f159a6c0d5007a1cff0c0b7746fceb10364.png',
    'Project/src/assets/images/7c93d7c36861a617e298e1137c2dc6a29a5f021b.png',
    'Project/src/assets/images/e57cb14a8560ce343df12846535d619ace8adf2e.png',
    'Project/src/assets/images/0a6c36e4de50eaf3ccc7b9a5282265163ad94604.png',
    'Project/src/assets/images/54d2311ab12f0f44cdc4a92c8faabb6c6ca034fb.png'
]:
    im = Image.open(f)
    print(f, im.size)
    # let's save a thumbnail to scratch to inspect
    im.resize((150, int(150 * im.size[1] / im.size[0]))).save(f"scratch/{f.split('/')[-1]}_thumb.jpg")

