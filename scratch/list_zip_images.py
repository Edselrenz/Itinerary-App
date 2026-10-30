import zipfile

with zipfile.ZipFile('Travel Itinerary App.fig', 'r') as z:
    for n in z.namelist():
        if 'a2a887' in n or '87a78d' in n or 'c56da46f24' in n:
            print("Found:", n)
    print("Total files in zip:", len(z.namelist()))
    # print all image names
    imgs = [n for n in z.namelist() if n.startswith('images/')]
    print(f"Total images: {len(imgs)}")

