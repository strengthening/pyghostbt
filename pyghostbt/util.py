import hashlib
import random
import math

from typing import List
from datetime import datetime

from pyanalysis.moment import moment
from pyghostbt.const import CONTRACT_TYPE_THIS_WEEK
from pyghostbt.const import CONTRACT_TYPE_NEXT_WEEK
from pyghostbt.const import CONTRACT_TYPE_QUARTER


def uuid() -> str:
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


def standard_number(input_num: float) -> int:
    """Get the standard num.

    In this project, the standard num is *100000000, and rounding to int.

    Args:
        input_num: The number you want to standard.

    Returns:
        The standard num.
    """
    if input_num > 0:
        return int(input_num * 100000000 + 0.5)
    return int(input_num * 100000000 - 0.5)


def real_number(std_num: float) -> float:
    return std_num / 100000000


def get_o_or_l_price(
        anchored_price: int = None,
        diff: int = None,
        open_times: int = None,
) -> List[int]:
    return [anchored_price + i * diff for i in range(open_times)]


def get_open_amount(
        total_asset: float = None,
        position: float = None,
        unit_amount: int = None,
        slippage: float = None,
        open_price: int = None,
        liquidate_price: int = None,
        open_times: int = 3,
        fee_rate: float = -0.0005,  # The fee_rate must be negative.
        scale: float = 1.0,
) -> List[int]:
    """Get the open amount array.

    The open amount is a complicated calculating process. This func calculate it for worst situation. Why complicated?
    1. total_asset包含了fee + 保证金。其中fee是损失，所以total_asset并不能当做净值计算open_amount。
    2. 开仓平仓会有滑点，滑点会带来fee的变动，以及open_amount的变动。

    故此方法假设，此次交易以最差的情况止损。并在开仓，平仓都有滑点的情况下完成交易。

    Args:
        total_asset: The total asset of the pair
        position: The position want to open.
        unit_amount: The contract unit amount.
        slippage: The slippage must be negative.
        open_price: The avg_price of open orders.
        liquidate_price: The avg_price of liquidate orders.
        open_times: The times to divide.
        fee_rate: The fee rate
        scale:

    Returns:
        amount array of each open times.
    """
    real_open_price = real_number(open_price)
    real_liquidate_price = real_number(liquidate_price)
    worst_real_price = min(real_open_price, real_liquidate_price)

    # 粗略的开仓张数
    open_amount = total_asset * position * worst_real_price * (1.0 + slippage) / unit_amount

    # 计算净资产
    max_open_fee = total_asset * position * fee_rate
    max_liquidate_fee = open_amount * unit_amount * fee_rate / (real_liquidate_price * (1.0 + slippage))
    net_asset = total_asset + max_open_fee + max_liquidate_fee
    open_amount = net_asset * position * worst_real_price * (1.0 + slippage) / unit_amount

    amounts: List[int] = []
    sum_scale = scale * open_times
    if scale != 1.0:
        sum_scale = (1 - math.pow(scale, open_times)) / (1 - scale)
    for i in range(open_times):
        amount = int(open_amount * math.pow(scale, i) / sum_scale)
        amounts.append(amount)
    return amounts


def get_contract_type(timestamp: int, due_timestamp: int) -> str:
    """Get the contract_type

    Input the timestamp and due_timestamp. Return which contract_type is.

    Args:
        timestamp: The target timestamp, you want to know.
        due_timestamp: The due timestamp of the contract.

    Returns:
        The contract_type name.

    Raises:
        RuntimeError: An error occurred timestamp gt due_timestamp.
    """
    minus = due_timestamp - timestamp
    if minus < 0:
        raise RuntimeError("the timestamp more than due_timestamp")
    if minus < 7 * 24 * 60 * 60 * 1000:
        return CONTRACT_TYPE_THIS_WEEK
    elif minus < 14 * 24 * 60 * 60 * 1000:
        return CONTRACT_TYPE_NEXT_WEEK
    else:
        return CONTRACT_TYPE_QUARTER


def get_contract_timestamp(timestamp: int, contract_type: str) -> (int, int, int):
    """Get the contract key timestamp info.

    The contract contain start, swap, due time, this func return the timestamps.

    Args:
        timestamp: The target timestamp, you want to know.
        contract_type: The contract type, must be this_week/ next_week/ quarter

    Returns:
        A tuple with three int result. It is the contract start_timestamp,
        swap_timestamp, due_timestamp.

    Raises:
        RuntimeError: An error occurred error contract_type
    """
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
