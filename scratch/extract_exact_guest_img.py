import zipfile

with zipfile.ZipFile('Travel Itinerary App.fig', 'r') as z:
    names = [f for f in z.namelist() if 'a2a887a78' in f]
    print("Found in zip:", names)
    if names:
        z.extract(names[0], 'scratch')
        print("Extracted to scratch/", names[0])

