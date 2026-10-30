with open('Project/decompressed_canvas.bin', 'rb') as f:
    data = f.read()

# Let's search for vector data around offset 101740 or 105882
chunk = data[105800:106200]
print(chunk)

