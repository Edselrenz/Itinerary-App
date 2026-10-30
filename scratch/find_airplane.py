with open('Project/decompressed_canvas.bin', 'rb') as f:
    data = f.read()

pos = 0
while True:
    pos = data.find(b'clarity:airplane-solid', pos)
    if pos == -1:
        break
    print(f"Found clarity:airplane-solid at {pos}")
    print(data[pos-100:pos+200])
    pos += 22

