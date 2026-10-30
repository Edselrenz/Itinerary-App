from PIL import Image

im = Image.open(r"C:/Users/Edward/.gemini/antigravity/brain/227d42fc-f285-416b-839a-2864eb1a7ab1/.user_uploaded/media_1793336850023_e7049ff9.jpg")
# Inside the screen:
# left=36, top=26, right=360, bottom=375
crop = im.crop((36, 26, 360, 375))
crop.save("scratch/crop_test.png")
print("Saved crop_test.png size:", crop.size)

