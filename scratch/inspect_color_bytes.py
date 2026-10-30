with open('Project/decompressed_canvas.bin', 'rb') as f:
    data = f.read()

for target in [b'Colors/Blue', b'Accents/Blue', b'Backgrounds/Primary', b'Grays/Gray 4']:
    pos = data.find(target)
    if pos != -1:
        chunk = data[pos-100:pos+100]
        print(f"Around {target}:", chunk)

