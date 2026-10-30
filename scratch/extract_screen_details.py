import re

with open('Project/decompressed_canvas.bin', 'rb') as f:
    data = f.read()

def search_context(target_phrase, window_size=500):
    pos = 0
    while True:
        pos = data.find(target_phrase.encode('utf-8'), pos)
        if pos == -1:
            break
        print(f"\n================ Target: {target_phrase} at {pos} ================")
        chunk = data[max(0, pos-window_size):min(len(data), pos+window_size)]
        # find ascii/utf-8 strings of length >= 2
        strings = re.findall(rb'[A-Za-z0-9 ,.!\'?()&/:@_#\-\+]{2,80}', chunk)
        for s in strings:
            decoded = s.decode('latin1', 'ignore').strip()
            if len(decoded) > 2:
                print("  ", decoded)
        pos += len(target_phrase)

for query in [
    'Welcome/Choose Start Screen',
    'Explore as a guest',
    'Home Page',
    'Suggested Itinerary',
    'Custom Itinerary',
    'Popular Destinations'
]:
    search_context(query, 350)

