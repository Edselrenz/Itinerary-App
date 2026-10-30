import re

with open('Project/decompressed_canvas.bin', 'rb') as f:
    data = f.read()

# Let's locate the exact blocks around "Welcome/Choose Start Screen" and "Home Page"
def dump_area(target, length=1500):
    pos = 0
    while True:
        pos = data.find(target if isinstance(target, bytes) else target.encode('utf-8'), pos)
        if pos == -1:
            break
        print(f"\n--- FOUND '{target}' at {pos} ---")
        window = data[max(0, pos-200):min(len(data), pos+length)]
        # Extract ASCII strings
        raw_strs = re.findall(rb'[\x20-\x7e]{3,60}', window)
        for s in raw_strs:
            dec = s.decode('latin1', 'ignore').strip()
            if len(dec) >= 3 and not re.match(r'^[0-9a-f]{16,}$', dec):
                print("  >", dec)
        pos += len(target)

print("=== WELCOME SCREEN AREA ===")
dump_area(b'Welcome/Choose Start Screen', 1200)

print("\n=== HOME PAGE AREA ===")
dump_area(b'Home Page', 2000)

