import re

with open('Project/decompressed_canvas.bin', 'rb') as f:
    data = f.read()

# Let's search for "characters" or examine kiwi schema
print("Header bytes:", data[:64])

# Let's search for "name" and "characters"
# In Kiwi schema, strings are usually stored with length-prefix or null-terminated.
# Let's look for readable text chunks > 5 characters that are not python/code artifacts
chunks = re.findall(rb'[\x20-\x7e]{4,80}', data)
# Filter out common binary artifacts, keep phrases with spaces
phrases = []
for c in chunks:
    s = c.decode('latin1').strip()
    if ' ' in s and not s.startswith('http') and not re.match(r'^[0-9a-fA-F\s]+$', s):
        phrases.append(s)

print(f"Total phrases found: {len(phrases)}")
unique_phrases = []
seen = set()
for p in phrases:
    if p not in seen:
        seen.add(p)
        unique_phrases.append(p)

for p in unique_phrases:
    if any(w in p for w in ['Trip', 'Guest', 'Welcome', 'Login', 'Sign', 'Itinerary', 'Custom', 'Suggested', 'Destination', 'Minalungao', 'Gapan', 'Pantabangan', 'Budget', 'Preference', 'Explore', 'Search', 'Plan', 'adventure', 'memories', 'Day 1', 'Day 2', 'Day 3', 'Terminal', 'Profile', 'History']):
        print("->", p)

