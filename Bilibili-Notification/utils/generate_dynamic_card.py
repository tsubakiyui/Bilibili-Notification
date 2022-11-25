#!/usr/bin/python
# coding:utf-8

import asyncio
from commons import wecomchan_robot
from configs import wecomchan_config
#
import base64
from io import BytesIO
from bilibili_dynamic import DynamicRender
from tests.dylist import dylist

'''
传入动态链接
返回BASE64

'''

Render = DynamicRender.DynamicPictureRendering(path="./tmp")


def im_2_b64(image):
    buff = BytesIO()
    image.save(buff, format="JPEG")
    img_str = base64.b64encode(buff.getvalue())
    return img_str


async def dynamicCard(dynamic):
    i = 0
    for element in dynamic:
        await Render.ReneringManage(element)
        image_base64 = im_2_b64(Render.ReprenderIMG)
        i += 1
        if i == 1:
            return image_base64


def convert(dynamic):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(dynamicCard(dynamic))


async def test(robot):
    i = 0
    for element in dylist:
        await Render.ReneringManage(element)
        # 您可以在实例化的类中的 ReprenderIMG 获得图片对象
        image_base64 = im_2_b64(Render.ReprenderIMG)
        # print(type(image_base64))
        robot.send_image(image_base64)
        i += 1
        if i == 1:
            break


if __name__ == "__main__":
    robot = wecomchan_robot.WoComChan(wecomchan_config.WOCOMCHAN_PUSH_ROBOT_WECOM_CID, \
                                      wecomchan_config.WOCOMCHAN_PUSH_ROBOT_WECOM_AID, \
                                      wecomchan_config.WOCOMCHAN_PUSH_ROBOT_WECOM_SEC
                                      )
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test())
