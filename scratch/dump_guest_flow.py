import re

with open('Project/decompressed_canvas.bin', 'rb') as f:
    data = f.read()

pos = 128833
chunk = data[pos-300:pos+1500]
strs = re.findall(rb'[\x20-\x7e]{3,80}', chunk)
print("Explore as a guest context:")
prev = None
for s in strs:
    dec = s.decode('latin1', 'ignore').strip()
    if len(dec) >= 3 and not re.match(r'^[0-9a-f]{20,}$', dec) and dec != prev:
        if any(c.isalpha() for c in dec):
            print(" -", dec)
            prev = dec

