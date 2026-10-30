import re

with open('Project/decompressed_canvas.bin', 'rb') as f:
    data = f.read()

# Let's find text strings that look like screen titles or UI labels
# Figma kiwi binary format has strings encoded as utf-8 or ascii with length prefixes
strings = re.findall(rb'[A-Za-z0-9 ,.!\'?()&/:@_#\-]{3,60}', data)
clean_strings = set()
for s in strings:
    text = s.decode('latin1', 'ignore').strip()
    if len(text) >= 3 and not text.startswith('__') and not all(c in '0123456789abcdef' for c in text.lower()):
        clean_strings.add(text)

# Let's look for UI frames / screens specifically
keywords = ['Welcome', 'Login', 'Sign up', 'Home', 'Explore', 'Itinerary', 'Suggested', 'Custom', 'Budget', 'Preference', 'Select', 'Destination', 'Route', 'Map', 'History', 'Profile', 'Minalungao', 'Cabanatuan', 'Gapan', 'Pantabangan', 'Trip', 'Search']

matches = [s for s in clean_strings if any(k.lower() in s.lower() for k in keywords)]
print(f"Total matching UI strings found: {len(matches)}")
for s in sorted(matches):
    print("-", s)

