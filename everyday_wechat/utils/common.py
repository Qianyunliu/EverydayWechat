# coding=utf-8
"""
工具类
"""
import re
import hashlib
import json

__all__ = [
    'FILEHELPER_MARK', 'FILEHELPER', 'SPIDER_HEADERS', 'WEEK_DICT',
    'BIRTHDAY_COMPILE', 'CONSTELLATION_NAME_LIST', 'CONSTELLATION_DATE_DICT',
    'is_json', 'md5_encode', 'get_constellation_name']

FILEHELPER_MARK = ['文件传输助手', 'filehelper']  # 文件传输助手标识
FILEHELPER = 'filehelper'

SPIDER_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; '
                  'WOW64; rv:60.0) Gecko/20100101 Firefox/60.0',
}

WEEK_DICT = {
    'Monday': '星期一', 'Tuesday': '星期二', 'Wednesday': '星期三',
    'Thursday': '星期四', 'Friday': '星期五', 'Saturday': '星期六',
    'Sunday': '星期日'
}

BIRTHDAY_COMPILE = re.compile(r'[\-\s]?(0?[1-9]|1[012])[\-\/\s]+(0?[1-9]|[12][0-9]|3[01])$')
CONSTELLATION_NAME_LIST = (
    "摩羯座", "水瓶座", "双鱼座", "白羊座",
    "金牛座", "双子座", "巨蟹座", "狮子座",
    "处女座", "天秤座", "天蝎座", "射手座")

CONSTELLATION_DATE_DICT = {
    (1, 20): '摩羯座',
    (2, 19): '水瓶座',
    (3, 21): '双鱼座',
    (4, 21): '白羊座',
    (5, 21): '金牛座',
    (6, 22): '双子座',
    (7, 23): '巨蟹座',
    (8, 23): '狮子座',
    (9, 23): '处女座',
    (10, 23): '天秤座',
    (11, 23): '天蝎座',
    (12, 23): '射手座',
    (12, 32): '摩羯座',
}


def is_json(resp):
    """
    判断数据是否能被 Json 化。 True 能，False 否。
    :param resp: request.
    :return: bool, True 数据可 Json 化；False 不能 JOSN 化。
    """
    try:
        json.loads(resp.text)
        return True
    except AttributeError as error:
        return False
    return False


def md5_encode(text):
    """ 把數據 md5 化 """
    if not isinstance(text, str):
        text = str(text)
    md5 = hashlib.md5()
    md5.update(text.encode('utf-8'))
    encodedStr = md5.hexdigest().upper()
    return encodedStr


def get_constellation_name(date):
    '''
    通过日期来返回星座名，或者檢查星座名是否正確。
    :param date: 指定日期或者星座名
    :return:rtype str
    '''
    if not date:
        return
    date = date.strip()
    if date in CONSTELLATION_NAME_LIST:
        return date

    times = BIRTHDAY_COMPILE.findall(date)
    if times:
        month, day = int(times[0][0]), int(times[0][1])
        for k, v in CONSTELLATION_DATE_DICT.items():
            if k > (month, day):
                return v
    return None


if __name__ == '__main__':
    print(md5_encode('aeryou'))
    pass
