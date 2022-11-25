#!/usr/bin/python
#coding:utf-8
import configs.dingding_config
from managers.service_manager import service_manager
from servers import notification_poll_service
from servers import dingding_push_service
from servers import sleep_cpu_service
from servers import wecomchan_push_service
from utils.wecom_send import send_markdown
import traceback

def main():
    service_manager.register_service(notification_poll_service.NotificationPollService())
    service_manager.register_service(dingding_push_service.DingdingPushService())
    service_manager.register_service(wecomchan_push_service.WeComchanPushService())
    service_manager.register_service(sleep_cpu_service.SleepCpuService())
    
    return service_manager.execute()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        send_markdown(text=str(traceback.format_exc()))
