import re

with open('Project/decompressed_canvas.bin', 'rb') as f:
    data = f.read()

# search for hex colors like #xxxxxx or color styles
hex_matches = re.findall(rb'#[0-9a-fA-F]{6}', data)
print("Hex colors in Figma:", set(m.decode() for m in hex_matches))

# search for "Colors/" or "Grays/"
color_names = re.findall(rb'(?:Colors|Grays|Backgrounds|Accents)/[A-Za-z0-9 _-]+', data)
print("Color style names:", set(c.decode() for c in color_names))

