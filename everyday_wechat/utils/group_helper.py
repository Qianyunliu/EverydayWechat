# -*- coding: utf-8 -*-
"""
Project: EverydayWechat-Github
Creator: DoubleThunder
Create time: 2019-07-11 12:55
Introduction: 群消息处理
"""

import re
from datetime import datetime
import itchat

from everyday_wechat.utils import config
from everyday_wechat.control.calendar.rt_calendar import get_rtcalendar
from everyday_wechat.utils.data_collection import (
    get_weather_info,
    get_bot_info,
    # get_calendar_info,
)
from everyday_wechat.control.rubbish.atoolbox_rubbish import (
    get_atoolbox_rubbish
)

from everyday_wechat.utils.db_helper import (
    find_perpetual_calendar,
    find_user_city,
    find_weather,
    udpate_user_city,
    udpate_weather,
    update_perpetual_calendar,
    find_rubbish,
    update_rubbish
)

__all__ = ['handle_group_helper']

at_compile = r'(@.*?\s{1,}).*?'
tomorrow_compile = r'明[日天]'

punct_complie = r'[^a-zA-z0-9\u4e00-\u9fa5]+$'  # 去除句子最后面的标点
help_complie = r'^(?:0|帮忙|帮助|help)\s*$'

weather_compile = r'^(?:\s*(?:1|天气|weather)(?!\d).*?|.*?(?:天气|weather)\s*)$'
weather_clean_compile = r'1|天气|weather|\s'
calendar_complie = r'^\s*(?:2|日历|万年历|calendar)(?=19|2[01]\d{2}|\s|$)'
calendar_date_compile = r'^\s*(19|2[01]\d{2})[\-\/—\s年]*(0?[1-9]|1[012])[\-\/—\s月]*(0?[1-9]|[12][0-9]|3[01])[\s日号]*$'
rubbish_complie = r'^\s*(?:3|垃圾|rubbish)(?!\d)'

common_msg = '@{ated_name}\u2005\n{text}'
weather_error_msg = '@{ated_name}\u2005\n未找到『{city}』城市的天气信息'
weather_null_msg = '@{ated_name}\u2005\n 请输入城市名'

calendar_error_msg = '@{ated_name}\u2005日期格式不对'
calendar_no_result_msg = '@{ated_name}\u2005未找到{_date}的数据'

rubbish_normal_msg = '@{ated_name}\u2005\n【查询结果】：『{name}』属于{_type}'
rubbish_other_msg = '@{ated_name}\u2005\n【查询结果】：『{name}』无记录\n【推荐查询】：{other}'
rubbish_nothing_msg = '@{ated_name}\u2005\n【查询结果】：『{name}』无记录'
rubbish_null_msg = '@{ated_name}\u2005 请输入垃圾名称'

help_group_content = """@{ated_name}
群助手功能：
1.输入：天气+城市名（可空）。例如：天气北京
2.输入：日历+日期(格式:yyyy-MM-dd 可空)。例如：日历2019-07-03
3.输入：垃圾+名称。例如：3猫粮
更多功能：请输入 help/帮助。
"""


# import pysnooper
# @pysnooper.snoop()
def handle_group_helper(msg):
    """
    处理群消息
    :param msg:
    :return:
    """

    conf = config.get('group_helper_conf')
    if not conf.get('is_open'):
        return
    text = msg['Text']

    # 如果开启了 『艾特才回复』，而群用户又没有艾特你。不处理消息
    if conf.get('is_at') and not msg.isAt:
        return

    uuid = msg.fromUserName  # 群 uid
    ated_uuid = msg.actualUserName  # 艾特你的用户的uuid
    ated_name = msg.actualNickName  # 艾特你的人的群里的名称

    is_all = conf.get('is_all', False)
    user_uuids = conf.get('group_black_uuids') if is_all else conf.get('group_white_uuids')
    # 开启回复所有群，而用户是黑名单，不处理消息
    if is_all and uuid in user_uuids:
        return

    # 未回复所有群，而用户不是白名单，不处理消息
    if not is_all and uuid not in user_uuids:
        return
    # 去掉 at 标记
    text = re.sub(at_compile, '', text)

    # 如果是帮助
    helps = re.findall(help_complie, text, re.I)
    if helps:
        retext = help_group_content.format(ated_name=ated_name)
        itchat.send(retext, uuid)
        return

    # 是否是明天，用于日历，天气，星座查询
    is_tomorrow = re.findall(tomorrow_compile, text)
    if is_tomorrow:
        is_tomorrow = True
        htext = re.sub(tomorrow_compile, '', text)
    else:
        is_tomorrow = False
        htext = text

    htext = re.sub(punct_complie, '', htext)  # 去句末的标点

    # 已开启天气查询，并包括天气关键词
    if conf.get('is_weather'):
        if re.findall(weather_compile, htext, re.I):
            city = re.sub(weather_clean_compile, '', text, flags=re.IGNORECASE).strip()

            if not city:  # 如果只是输入城市名
                # 从缓存数据库找最后一次查询的城市名
                city = find_user_city(ated_uuid)
            if not city:  # 缓存数据库没有保存，通过用户的资料查城市
                city = get_city_by_uuid(ated_uuid)
            if not city:
                retext = weather_null_msg.format(ated_name=ated_name)
                itchat.send(retext, uuid)
                return

            _date = datetime.now().strftime('%Y-%m-%d')
            weather_info = find_weather(_date, city)
            if weather_info:
                retext = common_msg.format(ated_name=ated_name, text=weather_info)
                itchat.send(retext, uuid)
                return

            weather_info = get_weather_info(city)
            if weather_info:
                # print(ated_name, city, retext)
                retext = common_msg.format(ated_name=ated_name, text=weather_info)
                itchat.send(retext, uuid)

                data = {
                    '_date': _date,
                    'city_name': city,
                    'weather_info': weather_info,
                    'userid': ated_uuid,
                    'last_time': datetime.now()
                }
                udpate_weather(data)
                # userid,city_name,last_time,group_name udpate_weather_city
                data2 = {
                    'userid': ated_uuid,
                    'city_name': city,
                    'last_time': datetime.now()
                }
                udpate_user_city(data2)
                return
            else:
                retext = weather_error_msg.format(ated_name=ated_name, city=city)
                itchat.send(retext, uuid)
                return
            return

    # 已开启日历，并包含日历
    if conf.get('is_calendar'):
        if re.findall(calendar_complie, htext, flags=re.IGNORECASE):

            calendar_text = re.sub(calendar_complie, '', htext).strip()
            if calendar_text:  # 日历后面填上日期了
                dates = re.findall(calendar_date_compile, calendar_text)
                if not dates:
                    retext = calendar_error_msg.format(ated_name=ated_name)
                    itchat.send(retext, uuid)
                    return

                _date = '{}-{:0>2}-{:0>2}'.format(*dates[0])  # 用于保存数据库
                rt_date = '{}{:0>2}{:0>2}'.format(*dates[0])  # 用于查询日历
            else:  # 日历 后面没有日期，则默认使用今日。
                _date = datetime.now().strftime('%Y-%m-%d')
                rt_date = datetime.now().strftime('%Y%m%d')

            # 从数据库缓存中记取内容
            cale_info = find_perpetual_calendar(_date)
            if cale_info:
                retext = common_msg.format(ated_name=ated_name, text=cale_info)
                itchat.send(retext, uuid)
                return

            # 取网络数据
            cale_info = get_rtcalendar(rt_date)
            if cale_info:
                retext = common_msg.format(ated_name=ated_name, text=cale_info)
                itchat.send(retext, uuid)
                update_perpetual_calendar(_date, cale_info)  # 保存数据到数据库
                return
            else:  # 查询无结果
                retext = calendar_no_result_msg.format(ated_name=ated_name, _date=_date)
                itchat.send(retext, uuid)
            return

    if conf.get('is_rubbish'):
        if re.findall(rubbish_complie, htext, re.I):
            key = re.sub(rubbish_complie, '', htext, flags=re.IGNORECASE).strip()
            if not key:
                retext = rubbish_null_msg.format(ated_name=ated_name)
                itchat.send(retext, uuid)
                return

            _type = find_rubbish(key)
            if _type:
                retext = rubbish_normal_msg.format(ated_name=ated_name, name=key, _type=_type)
                itchat.send(retext, uuid)
                return
            _type, return_list, other = get_atoolbox_rubbish(key)
            if _type:
                retext = rubbish_normal_msg.format(ated_name=ated_name, name=key, _type=_type)
                itchat.send_msg(retext, uuid)
            elif other:
                retext = rubbish_other_msg.format(ated_name=ated_name, name=key, other=other)
                itchat.send_msg(retext, uuid)
            else:
                retext = rubbish_nothing_msg.format(ated_name=ated_name, name=key)
                itchat.send_msg(retext, uuid)
            if return_list:
                update_rubbish(return_list)  # 保存数据库
            return

    # 其他结果都没有匹配到，走自动回复的路
    if conf.get('is_auto_reply'):
        reply_text = get_bot_info(text, ated_uuid)  # 获取自动回复
        if reply_text:  # 如内容不为空，回复消息
            reply_text = common_msg.format(ated_name=ated_name, text=reply_text)
            itchat.send(reply_text, uuid)
            print('回复{}：{}'.format(ated_name, reply_text))
        else:
            print('自动回复失败\n')


# 通过用户id找好友
def get_city_by_uuid(uid):
    """
    通过用户的uid得到用户的城市
    最好是与机器人是好友关系
    """
    itchat.get_friends(update=True)
    info = itchat.search_friends(userName=uid)
    # print('info:'+str(info))
    if not info:
        return None
    city = info.city
    # print('city:'+city)
    return city
