import re

with open('Project/decompressed_canvas.bin', 'rb') as f:
    data = f.read()

# Let's inspect occurrences of "Flow" or frame names
flow_matches = re.findall(rb'Flow [0-9]+', data)
print("Flow matches:", set(flow_matches))

# Look for patterns like "Page" or "Screen" or top-level names
matches = re.findall(rb'([A-Z][A-Za-z0-9 /_-]{2,40}(?:Screen|Page|View|Modal|Popup|Details|Card))', data)
print("Screen-like names:", set(m.decode('latin1') for m in matches))

# Let's list all text segments in the file that appear next to "Inter"
text_blocks = re.findall(rb'Inter(?:-Bold|-Regular|-Medium|-SemiBold)?\x00*([A-Za-z0-9 ,.!\'?()&/:@_#\-\+\n]{3,100})', data)
print(f"\nSample of text styled with Inter ({len(text_blocks)} items):")
for t in set(text_blocks[:60]):
    print("  *", t.decode('latin1', 'ignore').strip())

