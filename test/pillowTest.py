from PIL import Image
import requests
import numpy.random as random

url = 'https://uploads.mangadex.org/data/d0f38c13f77db764b4a06380cd83f5f9/3-e5540c209d2ddcf153b486010219c06c81c62525e0c5036c90a3de7e26c88733.png'

im = Image.open(requests.get(url, stream=True).raw)

width, height = im.size

# resize tall images
if width*3 < height:
    
    left = 0
    top = random.randint(0, height-width*3)
    right = width
    bottom = top + width*3

    im1 = im.crop((left, top, right, bottom))
 
    im1.show()

    im1 = im1.save("geeks.jpg")
    print(im1)