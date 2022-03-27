#!/usr/bin/python

#消息轮询服务
import time
import json
from collections import deque
from configs import services_config
from servers import service
from defines import event_type
from defines import message_type
from commons.dispatcher import dispatcher
from commons.bili_query import capturer
from utils.logger import logger
from utils.proxy import my_proxy

class NotificationPollService(service.Service):
    __bilibili_member_capturers = []
    __bilibili_official_capturers = []

    __dynamic_dict = {}         #记录各个成员间最新的动态id
    __living_status_dict = {}   #记录最新的直播状态
    __len_of_deque = 20         #
    def __init__(self):
        uid_list_member = services_config.UID_LIST_MEMBER
        uid_list_official = services_config.UID_LIST_OFFICIAL
        for _,uid in enumerate(uid_list_member):
            temp_capturer = capturer.BilibiliCapturer(uid)
            self.__bilibili_member_capturers.append(temp_capturer)
        for _,uid in enumerate(uid_list_official):
            temp_capturer = capturer.BilibiliCapturer(uid)
            self.__bilibili_official_capturers.append(temp_capturer)

    def _onUpdate(self):
        if not self.__is_in_poll_time():
            return 

        #成员动态轮询
        for _,capturer in enumerate(self.__bilibili_member_capturers):
            captured_uid = capturer.get_uid()
            captured_dynamic_content = capturer.capture_dynamic()
            if self.__verify_dynamic_is_ok(captured_uid,captured_dynamic_content):
                if self.__check_dynamic_is_new(captured_uid,captured_dynamic_content):
                    if self.__check_dynamic_is_can_push(captured_uid,captured_dynamic_content):
                        dispatcher.dispatch_event(event_type.MESSAGE_PUSH,{
                            'type' : message_type.MessageType.Dynamic,
                            'content' : self.__convert_dynamic_content_to_message(captured_uid,captured_dynamic_content)
                        })

            captured_live_status_content = capturer.capture_live_status()
            if self.__verify_live_status_is_ok(captured_uid,captured_live_status_content):
                if self.__check_live_status_is_new(captured_uid,captured_live_status_content):
                    dispatcher.dispatch_event(event_type.MESSAGE_PUSH,{
                        'type' : message_type.MessageType.Live,
                        'content' : self.__convert_live_status_content_to_message(captured_uid,captured_live_status_content)
                    })

        #官号公告轮询,不检查直播状态(很少情况在官号直播)
        for _,capturer in enumerate(self.__bilibili_official_capturers):
            captured_uid = capturer.get_uid()
            captured_dynamic_content = capturer.capture_dynamic()
            if self.__verify_dynamic_is_ok(captured_uid,captured_dynamic_content):
                if self.__check_dynamic_is_new(captured_uid,captured_dynamic_content):
                    if self.__check_dynamic_is_can_push(captured_uid,captured_dynamic_content):
                        dispatcher.dispatch_event(event_type.MESSAGE_PUSH,{
                            'type' : message_type.MessageType.Notice,
                            'content' : self.__convert_dynamic_content_to_message(captured_uid,captured_dynamic_content)
                        })

        time.sleep(services_config.INTERVALS_SECOND)
        
    #是否在轮询的时间内
    def __is_in_poll_time(self):
        current_time = time.strftime("%H:%M", time.localtime(time.time()))
        begin_time = services_config.BEGIN_TIME
        end_time = services_config.END_TIME
        if begin_time == '':
            begin_time = '00:00'
        if end_time == '':
            end_time = '23:59'

        return (begin_time <= current_time <= end_time)

    #验证内容是否正确
    def __verify_dynamic_is_ok(self,uid,content):
        if content == "" :
            return False

        if content['code'] != 0:
            logger.error('【查询动态状态】请求返回数据code错误：{code}'.format(code=content['code']))
            return False
        else:
            data = content['data']
            if len(data['cards']) == 0:
                logger.info('【查询动态状态】【{uid}】动态列表为空'.format(uid=uid))
                return False

            item = data['cards'][0]
            try:
                _ = item['desc']['user_profile']['info']['uname']
            except KeyError:
                logger.error('【查询动态状态】【{uid}】获取不到uname'.format(uid=uid))
                return False
        
        return True

    def __verify_live_status_is_ok(self,uid,content):
        if content == "" :
            return False

        if content['code'] != 0:
            logger.error('【查询直播状态】请求返回数据code错误：{code}'.format(code=content['code']))
            return False 
        try:
            _ = content['data']['live_room']['liveStatus']
        except (KeyError, TypeError):
            logger.error('【查询动态状态】【{uid}】获取不到liveStatus'.format(uid=uid))
            return False

        return True

    #是否为最新的动态
    def __check_dynamic_is_new(self,uid,content):
        data = content['data']
        item = data['cards'][0] #获取最新的一条
        uname = item['desc']['user_profile']['info']['uname']
        dynamic_id = item['desc']['dynamic_id']
        if self.__dynamic_dict.get(uid, None) is None:
            self.__dynamic_dict[uid] = deque(maxlen=self.__len_of_deque)
            cards = data['cards']
            for index in range(self.__len_of_deque):
                if index < len(cards):
                    self.__dynamic_dict[uid].appendleft(cards[index]['desc']['dynamic_id'])
            logger.info('【查询动态状态】【{uname}】动态初始化：{queue}'.format(uname=uname, queue=self.__dynamic_dict[uid]))
            return False

        if dynamic_id not in self.__dynamic_dict[uid]:
            previous_dynamic_id = self.__dynamic_dict[uid].pop()
            logger.info('【查询动态状态】【{}】上一条动态id[{}]，本条动态id[{}]'.format(uname, previous_dynamic_id, dynamic_id))
            self.__dynamic_dic[uid].append(dynamic_id)
            logger.info(self.__dynamic_dic[uid])
            return True

        return False
    
    def __check_dynamic_is_can_push(self,uid,content):
        data = content['data']
        item = data['cards'][0] #获取最新的一条
        uname = item['desc']['user_profile']['info']['uname']
        dynamic_type = item['desc']['type']
        if dynamic_type not in services_config.HANDLE_DYNAMIC_TYPES:
            logger.info('【查询动态状态】【{uname}】动态有更新，但不在需要推送的动态类型列表中'.format(uname=uname))
            return False
        return True

    def __check_live_status_is_new(self,uid,content):
        name = content['data']['name']
        live_status = content['data']['live_room']['liveStatus']
        if self.__living_status_dict.get(uid, None) is None:
            self.__living_status_dict[uid] = live_status
            logger.info('【查询直播状态】【{uname}】初始化'.format(uname=name))
            return False

        if self.__living_status_dict.get(uid, None) != live_status:
            self.__living_status_dict[uid] = live_status

            room_title = content['data']['live_room']['title']

            if live_status == 1:
                logger.info('【查询直播状态】【{name}】开播了，准备推送：{room_title}'.format(name=name, room_title=room_title))
                return True
        
        return False

    #TODO:将内容转换成消息推送
    def __convert_dynamic_content_to_message(self,uid,content):
        data = content['data']
        item = data['cards'][0] #获取最新的一条
        uname = item['desc']['user_profile']['info']['uname']
        dynamic_type = item['desc']['type']
        timestamp = item['desc']['timestamp']
        dynamic_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
        card_str = item['card']
        card = json.loads(card_str)

        content = None
        pic_url = None
        if dynamic_type == 1:
            # 转发动态
            content = card['item']['content']
        elif dynamic_type == 2:
            # 图文动态
            content = card['item']['description']
            pic_url = card['item']['pictures'][0]['img_src']
        elif dynamic_type == 4:
            # 文字动态
            content = card['item']['content']
        elif dynamic_type == 8:
            # 投稿动态
            content = card['title']
            pic_url = card['pic']
        elif dynamic_type == 64:
            # 专栏动态
            content = card['title']
            pic_url = card['image_urls'][0]
        
        return content

    #TODO:
    def __convert_live_status_content_to_message(self,uid,content):
        room_id = content['data']['live_room']['roomid']
        room_title = content['data']['live_room']['title']
        room_cover_url = content['data']['live_room']['cover']


    def _onStart(self):
        if services_config.PROXY_ENABLE:
            my_proxy.proxy_pool_url = services_config.PROXY_POOL_URL
            my_proxy.current_proxy_ip = my_proxy.get_proxy()
            