import zipfile

with open('Project/decompressed_canvas.bin', 'rb') as f:
    data = f.read()

pos = 128833
chunk = data[pos-10000:pos+10000]

with zipfile.ZipFile('Travel Itinerary App.fig', 'r') as z:
    imgs = [n.replace('images/', '') for n in z.namelist() if n.startswith('images/') and len(n.replace('images/', '')) == 40]

print("Valid img hashes in zip:", len(imgs))
found = []
for img in imgs:
    raw = bytes.fromhex(img)
    p = chunk.find(raw)
    if p != -1:
        found.append((p, img))

print("Found image hashes near 128833:", found)

