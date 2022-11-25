#!/usr/bin/python
# coding:utf-8
import base64
from io import BytesIO

import requests
import sys
sys.path.append("../")
from commons import wecomchan_robot
from configs import wecomchan_config


robot = wecomchan_robot.WoComChan(wecomchan_config.WOCOMCHAN_PUSH_ROBOT_WECOM_CID, \
                                  wecomchan_config.WOCOMCHAN_PUSH_ROBOT_WECOM_AID, \
                                  wecomchan_config.WOCOMCHAN_PUSH_ROBOT_WECOM_SEC,\
                                  wecomchan_config.WOCOMCHAN_PUSH_ROBOT_WECOM_TID
                                  )

def im_2_b64(image):
    buff = BytesIO()
    image.save(buff, format="JPEG")
    img_str = base64.b64encode(buff.getvalue())
    return img_str

def send_markdown(text):
    robot.send_markdown(text=text)


def send_image_url(url):
    res = requests.request(url=url, method='get').content
    robot.send_image(base64.b64encode(res, altchars=None))


def send_image(url):
    base64 = im_2_b64(url)
    robot.send_image(base64_content=base64)


if __name__ == "__main__":
    print("wecom_send_markdown")
    robot.send_imageCard_Test()
