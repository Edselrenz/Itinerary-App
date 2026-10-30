import re
import zipfile

with open('Project/decompressed_canvas.bin', 'rb') as f:
    data = f.read()

with zipfile.ZipFile('Travel Itinerary App.fig', 'r') as z:
    image_names = [f.replace('images/', '') for f in z.namelist() if f.startswith('images/') and not f.endswith('/')]

print(f"Searching {len(image_names)} image hashes in decompressed canvas...")
for img in image_names:
    raw_hash = bytes.fromhex(img)
    pos = 0
    found_any = False
    while True:
        pos = data.find(raw_hash, pos)
        if pos == -1:
            break
        found_any = True
        window = data[max(0, pos-250):min(len(data), pos+250)]
        strings = re.findall(rb'[A-Za-z0-9 _\-.\'\"/]{4,50}', window)
        clean = [s.decode('latin1', 'ignore').strip() for s in strings if len(s.strip()) > 3]
        print(f"[{img[:8]}] offset {pos}: {clean}")
        pos += len(raw_hash)

