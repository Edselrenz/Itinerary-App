import zipfile

with open('Project/decompressed_canvas.bin', 'rb') as f:
    data = f.read()

pos = 128833
chunk = data[pos-1000:pos+1000]

with zipfile.ZipFile('Travel Itinerary App.fig', 'r') as z:
    imgs = [n.replace('images/', '') for n in z.namelist() if n.startswith('images/')]

found = []
for img in imgs:
    raw = bytes.fromhex(img)
    p = chunk.find(raw)
    if p != -1:
        found.append((p, img))

print("Found image hashes near 128833:", found)
if not found:
    # Let's search in window 5000
    chunk2 = data[pos-5000:pos+5000]
    for img in imgs:
        raw = bytes.fromhex(img)
        p = chunk2.find(raw)
        if p != -1:
            found.append((p, img))
    print("Found image hashes near 128833 (window 5000):", found)

