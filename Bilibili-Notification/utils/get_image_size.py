# coding:utf-8
import urllib.request
import io
from PIL import Image


def get_image_size(url):
    file = urllib.request.urlopen(url).read()
    tmp_img = io.BytesIO(file)
    img = Image.open(tmp_img)
    length, width = img.size
    size = round(length / width, 2)
    if size < 1.3:
        size = 1.3
    elif size > 2.25:
        size = 2.25
    return size

