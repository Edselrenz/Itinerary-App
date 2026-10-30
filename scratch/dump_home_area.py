import re

with open('Project/decompressed_canvas.bin', 'rb') as f:
    data = f.read()

# Let's inspect from offset 400 to 25000
chunk = data[400:30000]
# Extract all sequences of printable characters length >= 3
strs = re.findall(rb'[\x20-\x7e]{3,80}', chunk)
print("Strings in Home Page area (offset 400 to 30000):")
prev = None
for s in strs:
    dec = s.decode('latin1', 'ignore').strip()
    if len(dec) >= 3 and not re.match(r'^[0-9a-f]{20,}$', dec) and dec != prev:
        print(" -", dec)
        prev = dec

