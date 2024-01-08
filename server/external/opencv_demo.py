#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import cv2
from PIL import Image


def resize_img(image_file):
    image = Image.open(image_file)
    width, height = image.size
    if width != 2688 or height != 1520:
        image = image.resize((2688, 1520), Image.BILINEAR)
        image.save(image_file)


print(cv2.getVersionString())

resize_img("./data/camera0.jpg")
resize_img("./data/camera1.jpg")
