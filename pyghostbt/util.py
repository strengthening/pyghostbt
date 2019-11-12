import hashlib
import random
from datetime import datetime

from pyanalysis.moment import moment
from pyghostbt.const import *


def uuid():
    """
    generate uuid
    :return: the uuid len 32
    """
    m = hashlib.md5()
    m.update("{}{}".format(
        datetime.now().timestamp(),
        random.randint(1, 10000),
    ).encode())
    return m.hexdigest()


def get_contract_type(timestamp, due_timestamp):
    minus = due_timestamp - timestamp
    if minus < 0:
        raise RuntimeError("the timestamp more than due_timestamp")
    if minus < 7 * 24 * 60 * 60 * 1000:
        return CONTRACT_TYPE_THIS_WEEK
    elif minus < 14 * 24 * 60 * 60 * 1000:
        return CONTRACT_TYPE_NEXT_WEEK
    else:
        return CONTRACT_TYPE_QUARTER


def get_contract_timestamp(timestamp, contract_type):
    m = moment.get(timestamp).to("Asia/Shanghai")
    weekday = m.weekday()
    hour = m.hour
    if weekday < 4 or (weekday == 4 and hour < 16):
        m_this_week = m.floor("day").shift(days=4 - weekday, hours=16)
    else:
        m_this_week = m.floor("day").shift(days=6 - weekday + 5, hours=16)

    if contract_type == CONTRACT_TYPE_THIS_WEEK:
        due_timestamp = m_this_week.millisecond_timestamp
        start_timestamp = m_this_week.shift(days=-7).millisecond_timestamp
        swap_timestamp = start_timestamp
    elif contract_type == CONTRACT_TYPE_NEXT_WEEK:
        due_timestamp = m_this_week.shift(days=7).millisecond_timestamp
        swap_timestamp = m_this_week.millisecond_timestamp
        start_timestamp = m_this_week.shift(days=-7).millisecond_timestamp
    elif contract_type == CONTRACT_TYPE_QUARTER:
        # 3， 6， 9， 12月的最后一个周五。
        m_flag = m_this_week.shift(days=14)
        while m_flag.month not in (3, 6, 9, 12):
            m_flag = m_flag.shift(days=7)

        # 所在月份的最后一天
        m_flag = m_flag.ceil("month").floor("day").shift(hours=16)
        while m_flag.weekday() != 4:
            m_flag = m_flag.shift(days=-1)

        due_timestamp = m_flag.millisecond_timestamp
        swap_timestamp = m_flag.shift(days=-14).millisecond_timestamp

        m_flag = m_flag.shift(days=-105).ceil("month").floor("day")
        while m_flag.weekday() != 4:
            m_flag = m_flag.shift(days=-1)
        start_timestamp = m_flag.shift(days=-14, hours=16).millisecond_timestamp
    else:
        raise RuntimeError("Can not deal with the contract_type: " + contract_type)
    return start_timestamp, swap_timestamp, due_timestamp
