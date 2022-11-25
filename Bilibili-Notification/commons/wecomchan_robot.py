#!/usr/bin/python
# coding:utf-8

import requests
import base64
import json
from utils import http_util
from utils.logger import logger
from utils.get_image_size import get_image_size

# 企业微信推送
WOCOMCHAN_PUSH_SEND_URL = "https://qyapi.weixin.qq.com/cgi-bin/message"
WOCOMCHAN_PUSH_TOKEN_URL = "https://qyapi.weixin.qq.com/cgi-bin"
WOCOMCHAN_PUSH_MEDIA_URL = "https://qyapi.weixin.qq.com/cgi-bin/media"
# 企业微信推送接口
WOCOMCHAN_PUSH_WEBHOOK_TOKEN_ACTION = "gettoken"
WOCOMCHAN_PUSH_WEBHOOK_SEND_ACTION = "send"
WOCOMCHAN_PUSH_WEBHOOK_UPLOAD_ACTION = "upload"
# 企业微信推送token字段
WOCOMCHAN_PUSH_WEBHOOK_TOKEN_FIELD = "access_token"
WOCOMCHAN_PUSH_WEBHOOK_CORPID_FIELD = "corpid"
WOCOMCHAN_PUSH_WEBHOOK_CORPSECRET_FIELD = "corpsecret"
WOCOMCHAN_PUSH_WEBHOOK_TYPE_FIELD = "type"


class WoComChan:
    __wecom_cid = ""
    __wecom_aid = ""
    __wecom_secret = ""
    __wecom_touid = ""
    __wecom_token = ""
    __wecom_media_id = ""
    __wecom_base64_content = ""
    __wecom_type = ""

    def __init__(self, wecom_cid, wecom_aid, wecom_secret, wecom_touid):
        self.__wecom_cid = wecom_cid
        self.__wecom_aid = wecom_aid
        self.__wecom_secret = wecom_secret
        self.__wecom_touid = wecom_touid

    def get_send_url(cls, attrs=None):
        attrStr = ""
        if attrs != None:
            for k, v in attrs.items():
                attrStr = attrStr + "{0}={1}".format(k, v) + "&"
            attrStr.strip('&')

        return "{0}/{1}?{2}".format(WOCOMCHAN_PUSH_SEND_URL, WOCOMCHAN_PUSH_WEBHOOK_SEND_ACTION, attrStr)

    def get_token_url(cls, attrs=None):
        attrStr = ""
        if attrs != None:
            for k, v in attrs.items():
                attrStr = attrStr + "{0}={1}".format(k, v) + "&"
            attrStr.strip('&')

        return "{0}/{1}?{2}".format(WOCOMCHAN_PUSH_TOKEN_URL, WOCOMCHAN_PUSH_WEBHOOK_TOKEN_ACTION, attrStr)

    def get_upload_url(cls, attrs=None):
        attrStr = ""
        if attrs != None:
            for k, v in attrs.items():
                attrStr = attrStr + "{0}={1}".format(k, v) + "&"
            attrStr.strip('&')

        return "{0}/{1}?{2}".format(WOCOMCHAN_PUSH_MEDIA_URL, WOCOMCHAN_PUSH_WEBHOOK_UPLOAD_ACTION, attrStr)

    def send_markdown(self, text=""):
        data = {
            "touser": self.__wecom_touid,
            "agentid": self.__wecom_aid,
            "msgtype": "markdown",
            "markdown": {
                "content": text
            },
            "duplicate_check_interval": 600
        }
        self.get_token(data)

    def send_imageCard(self, icon_url, uname, title, image_url, dynamic_url, text="default"):
        data = {
            "touser": self.__wecom_touid,
            "msgtype": "template_card",
            "agentid": self.__wecom_aid,
            "template_card": {
                "card_type": "news_notice",
                "source": {
                    "icon_url": icon_url,
                    "desc": uname,
                    "desc_color": 1
                },
                "main_title": {
                    "title": title,
                    "desc": ""
                },
                "card_image": {
                    "url": image_url,
                    # 图片的宽高比，宽高比要小于2.25，大于1.3，不填该参数默认1.3
                    "aspect_ratio": get_image_size(image_url)
                },
                "vertical_content_list": [
                    {
                        "title": title,
                        "desc": text
                    }
                ],
                "jump_list": [
                    {
                        "type": 1,
                        "title": "查看",
                        "url": dynamic_url
                    }
                ],
                "card_action": {
                    "type": 1,
                    "url": dynamic_url,
                }
            },
            "enable_id_trans": 0,
            "enable_duplicate_check": 0,
            "duplicate_check_interval": 600
        }
        self.get_token(data)

    def send_image(self, base64_content):
        self.__wecom_base64_content = base64_content
        self.__wecom_type = "image"
        data = {
            "touser": self.__wecom_touid,
            "agentid": self.__wecom_aid,
            "msgtype": "image",
            "image": {
                "media_id": self.__wecom_media_id
            },
            "duplicate_check_interval": 600
        }
        self.get_token(data)

    def get_media_id(self):
        attr_dict = {}

        if self.__wecom_token != "":
            attr_dict[WOCOMCHAN_PUSH_WEBHOOK_TOKEN_FIELD] = self.__wecom_token

        if self.__wecom_type != "":
            attr_dict[WOCOMCHAN_PUSH_WEBHOOK_TYPE_FIELD] = self.__wecom_type

        upload_url = self.get_upload_url(attr_dict)

        # response = http_util.requests_post(url=upload_url, files={
        #         "picture": base64.b64decode(self.__wecom_base64_content)
        #     }).json()
        response = requests.post(upload_url, files={
            "picture": base64.b64decode(self.__wecom_base64_content)
        }).json()
        if "media_id" in response:
            self.__wecom_media_id = response['media_id']
        else:
            return False

    def get_token(self, data):
        attr_dict = {}

        if self.__wecom_cid != "":
            attr_dict[WOCOMCHAN_PUSH_WEBHOOK_CORPID_FIELD] = self.__wecom_cid

        if self.__wecom_secret != "":
            attr_dict[WOCOMCHAN_PUSH_WEBHOOK_CORPSECRET_FIELD] = self.__wecom_secret

        send_url = self.get_token_url(attr_dict)
        response = http_util.requests_post(url=send_url, json=data).content
        access_token = json.loads(response).get('access_token')
        if access_token and len(access_token) > 0:
            self.__wecom_token = access_token
            if data["msgtype"] == "image":
                self.get_media_id()
                data["image"]["media_id"] = self.__wecom_media_id
            self.send(data)
        else:
            logger.error('【企业微信推送】出错')
            return False

    def send(self, data):
        attr_dict = {}

        if self.__wecom_token != "":
            attr_dict[WOCOMCHAN_PUSH_WEBHOOK_TOKEN_FIELD] = self.__wecom_token

        send_url = self.get_send_url(attr_dict)

        response = http_util.requests_post(url=send_url, json=data)
        if http_util.check_response_is_ok(response):
            try:
                result = json.loads(str(response.content, 'utf-8'))
                if result['errcode'] != 0:
                    logger.error('【企业微信推送】{} , data : {}'.format(result['errmsg'], data))
                return result
            except UnicodeDecodeError:
                logger.error('【企业微信推送】解析content出错')

    def send_to_wecom(self, text, wecom_cid, wecom_aid, wecom_secret, wecom_touid='@all'):
        get_token_url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={wecom_cid}&corpsecret={wecom_secret}"
        response = requests.get(get_token_url).content
        access_token = json.loads(response).get('access_token')
        if access_token and len(access_token) > 0:
            send_msg_url = f'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}'
            data = {
                "touser": wecom_touid,
                "agentid": wecom_aid,
                "msgtype": "text",
                "text": {
                    "content": text
                },
                "duplicate_check_interval": 600
            }
            response = requests.post(send_msg_url, data=json.dumps(data)).content
            return response
        else:
            return False

    def send_to_wecom_image(self, base64_content, wecom_cid, wecom_aid, wecom_secret, wecom_touid='@all'):
        get_token_url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={wecom_cid}&corpsecret={wecom_secret}"
        response = requests.get(get_token_url).content
        access_token = json.loads(response).get('access_token')
        if access_token and len(access_token) > 0:
            upload_url = f'https://qyapi.weixin.qq.com/cgi-bin/media/upload?access_token={access_token}&type=image'
            upload_response = requests.post(upload_url, files={
                "picture": base64.b64decode(base64_content)
            }).json()
            if "media_id" in upload_response:
                media_id = upload_response['media_id']
            else:
                return False

            send_msg_url = f'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}'
            data = {
                "touser": wecom_touid,
                "agentid": wecom_aid,
                "msgtype": "image",
                "image": {
                    "media_id": media_id
                },
                "duplicate_check_interval": 600
            }
            response = requests.post(send_msg_url, data=json.dumps(data)).content
            return response
        else:
            return False

    def send_to_wecom_markdown(text, wecom_cid, wecom_aid, wecom_secret, wecom_touid='@all'):
        get_token_url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={wecom_cid}&corpsecret={wecom_secret}"
        response = requests.get(get_token_url).content
        access_token = json.loads(response).get('access_token')
        if access_token and len(access_token) > 0:
            send_msg_url = f'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}'
            data = {
                "touser": wecom_touid,
                "agentid": wecom_aid,
                "msgtype": "markdown",
                "markdown": {
                    "content": text
                },
                "duplicate_check_interval": 600
            }
            response = requests.post(send_msg_url, data=json.dumps(data)).content
            return response
        else:
            return False
