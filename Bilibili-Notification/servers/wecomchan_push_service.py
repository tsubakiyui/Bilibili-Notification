#!/usr/bin/python

# 轮询推送服务
import queue
import time
import json
import traceback

from commons import wecomchan_robot
from servers import service
from defines import event_type
from defines import message_type
from configs import wecomchan_config
from configs import language_config
from commons.dispatcher import dispatcher
from utils.logger import logger
from utils.generate_dynamic_card import convert

class WeComchanPushService(service.Service):
    __dynamic_robot = None  # 动态推送
    __live_robot = None  # 直播状态推送
    __notice_robot = None  # 官号公告推送
    __message_queue = queue.Queue()  # 推送队列

    def __init__(self):
        super().__init__()
        self.__dynamic_robot = wecomchan_robot.WoComChan(wecomchan_config.WOCOMCHAN_PUSH_ROBOT_WECOM_CID, \
                                                         wecomchan_config.WOCOMCHAN_PUSH_ROBOT_WECOM_AID, \
                                                         wecomchan_config.WOCOMCHAN_PUSH_ROBOT_WECOM_SEC,\
                                                         wecomchan_config.WOCOMCHAN_PUSH_ROBOT_WECOM_TID
                                                         )
        self.__live_robot = wecomchan_robot.WoComChan(wecomchan_config.WOCOMCHAN_PUSH_ROBOT_WECOM_CID, \
                                                      wecomchan_config.WOCOMCHAN_PUSH_ROBOT_WECOM_AID, \
                                                      wecomchan_config.WOCOMCHAN_PUSH_ROBOT_WECOM_SEC,\
                                                         wecomchan_config.WOCOMCHAN_PUSH_ROBOT_WECOM_TID
                                                      )
        self.__notice_robot = wecomchan_robot.WoComChan(wecomchan_config.WOCOMCHAN_PUSH_ROBOT_WECOM_CID, \
                                                        wecomchan_config.WOCOMCHAN_PUSH_ROBOT_WECOM_AID, \
                                                        wecomchan_config.WOCOMCHAN_PUSH_ROBOT_WECOM_SEC,\
                                                         wecomchan_config.WOCOMCHAN_PUSH_ROBOT_WECOM_TID
                                                        )

    def _onUpdate(self):
        while not self.__message_queue.empty():
            msg = self.__message_queue.get()
            msg_type = msg['type']
            msg_title = msg['title']
            msg_text = msg['text']

            append = msg['append']
            append_uname = append['uname']
            append_icon_url = append['icon_url']
            append_title = append['title']
            append_image_url = append['image_url']
            append_content = append['content']
            append_open_url = append['open_url']

            logger.info('【推送服务机{type}】准备推送:【{title}】'.format(type=msg_type, title=msg_title))
            if msg_type == message_type.MessageType.Dynamic:
                # 发送DynamicCard
                if wecomchan_config.send_DynamicCard:
                    # 读取DynamicCard
                    append_dynamic_card = append['dynamic_card']
                    try:
                        # 将动态转换为DynamicCard
                        dynamic_card = convert(append_dynamic_card)
                        # 发送DynamicCard
                        self.__dynamic_robot.send_image(dynamic_card)
                    except Exception:
                        self.__dynamic_robot.send_markdown(text=str(traceback.format_exc()))
                # 发送ImageCard
                if wecomchan_config.send_ImageCard:
                    if append_image_url != '':
                        try:
                            self.__dynamic_robot.send_imageCard(append_icon_url, append_uname, append_title, \
                                                                append_image_url, append_open_url, append_content)
                        except Exception:
                            self.__dynamic_robot.send_markdown(text=str(traceback.format_exc()))
                # 发送MarkDown
                if wecomchan_config.send_MarkDown:
                    self.__dynamic_robot.send_markdown(text=msg_text)



            elif msg_type == message_type.MessageType.Live:
                if wecomchan_config.send_ImageCard:
                    try:
                        self.__live_robot.send_imageCard(append_icon_url, append_uname, append_title, \
                                                         append_image_url, append_open_url, append_content)
                    except Exception:
                        self.__live_robot.send_markdown(text=str(traceback.format_exc()))
                if wecomchan_config.send_MarkDown:
                    self.__live_robot.send_markdown(text=msg_text)

            elif msg_type == message_type.MessageType.Notice:
                self.__notice_robot.send_markdown(text=msg_text)

    def __push_message(self, msg):
        msg_type = msg['type']
        msg_item = msg['item']

        title, text, append = None, None, None
        if msg_type == message_type.MessageType.Dynamic:
            title, text, append = self.__convert_dynamic_content_to_message(msg_item)
        elif msg_type == message_type.MessageType.Live:
            title, text, append = self.__convert_live_status_content_to_message(msg_item)
        elif msg_type == message_type.MessageType.Notice:
            title, text, append = self.__convert_dynamic_content_to_message(msg_item)

        if title and text:
            self.__message_queue.put({
                'type': msg_type,
                'title': title,
                'text': text,
                'append': append
            })

    # 将内容转换成消息推送
    def __convert_dynamic_content_to_message(self, item):
        uid = item['desc']['uid']
        uname = item['desc']['user_profile']['info']['uname']
        dynamic_type = item['desc']['type']
        dynamic_id = item['desc']['dynamic_id']
        timestamp = item['desc']['timestamp']
        dynamic_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
        card_str = item['card']
        card = json.loads(card_str)

        # append
        icon_url = item['desc']['user_profile']['info']['face']

        content = ''
        pic_tags = ''
        if dynamic_type == 1:
            # 转发动态
            content = card['item']['content']

            # append
            title = f"{uname}转发了动态"
        elif dynamic_type == 2:
            # 图文动态
            content = card['item']['description']
            pic_url = card['item']['pictures'][0]['img_src']
            pic_tags = "[pic]({pic_url})".format(pic_url=pic_url)

            # append
            title = f"{uname}的动态更新"
            image_url = card['item']['pictures'][0]['img_src']

        elif dynamic_type == 4:
            # 文字动态
            content = card['item']['content']

            # append
            title = f"{uname}的动态更新"
            image_url = ''
        elif dynamic_type == 8:
            # 投稿动态
            # content = card['title']
            pic_url = card['pic']
            pic_tags = "[pic]({pic_url})".format(pic_url=pic_url)

            # append
            title = card['title']
            content = card['desc']
            image_url = card['pic']

        elif dynamic_type == 64:
            # 专栏动态
            content = card['title']
            pic_url = card['image_urls'][0]
            pic_tags = "[pic]({pic_url})".format(pic_url=pic_url)

            # append
            image_url = card['image_urls'][0]

        # append
        append = dict()
        append['uname'] = uname
        append['icon_url'] = icon_url
        append['title'] = title if 'title' in dir() else 'No title'
        append['image_url'] = image_url if 'image_url' in dir() else ''
        append['content'] = content
        append['open_url'] = f'https://t.bilibili.com/{dynamic_id}'

        append['dynamic_card'] = [item]

        '''
        在传数据时解决content
        '''

        if dynamic_type == 8:
            content = title + content

        return language_config.get_string_wecom(1000001, name=uname), language_config.get_string_wecom(1000002, name=uname,
                                                                                           content=content,
                                                                                           pic_tags=pic_tags,
                                                                                           dynamic_id=dynamic_id), append

    def __convert_live_status_content_to_message(self, content):
        print(content)
        name = content['data']['name']
        room_id = content['data']['live_room']['roomid']
        room_title = content['data']['live_room']['title']
        room_cover_url = content['data']['live_room']['cover']
        pic_tags = "[pic]({pic_url})".format(pic_url=room_cover_url)

        append = dict()
        append['uname'] = name
        append['icon_url'] = content['data']['face']
        append['title'] = room_title
        append['image_url'] = room_cover_url
        append['content'] = ''
        append['open_url'] = f'https://live.bilibili.com/{room_id}'

        return language_config.get_string(1000003, name=name), language_config.get_string(1000004, name=name,
                                                                                          content=room_title,
                                                                                          pic_tags=pic_tags,
                                                                                          room_id=room_id), append

    def _onStart(self):
        dispatcher.add_event_listener(event_type.MESSAGE_PUSH, self.__push_message)

    def _onExit(self):
        dispatcher.remove_event_listener(event_type.MESSAGE_PUSH, self.__push_message)
