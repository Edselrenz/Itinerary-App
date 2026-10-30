from PIL import Image

im = Image.open(r"C:/Users/Edward/.gemini/antigravity/brain/227d42fc-f285-416b-839a-2864eb1a7ab1/.user_uploaded/media_1793332685774_b6884c9f.jpg")
# Header is roughly y=90 to y=180, x=50 to x=360
crop = im.crop((50, 90, 360, 200))
crop.save(r"scratch/header_crop.png")
print("Saved header crop. Size:", crop.size)

