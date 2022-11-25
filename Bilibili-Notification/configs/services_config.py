#!/usr/bin/python
#coding:utf-8
# up主uid列表，使用英文逗号分隔，必填
UID_LIST_MEMBER = []
UID_LIST_OFFICIAL = []

# 需要处理的动态类型,目前支持:1转发动态,2图文动态,4文字动态,8投稿动态,64专栏动态
HANDLE_DYNAMIC_TYPES = [1, 2, 4, 6, 8, 64]

# 扫描间隔秒数，不建议设置太频繁
INTERVALS_SECOND = 30
# 扫描起止时间，24小时制(目前不支持跨日期)，例：07:00、23:59
BEGIN_TIME = "00:01"
END_TIME = "23:59"

#[proxy_pool]
# 是否启用 true/false
PROXY_ENABLE = False
# ip池地址，参考 https://github.com/jhao104/proxy_pool
PROXY_POOL_URL = "http://ip:port"