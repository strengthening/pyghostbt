import hashlib
import random
import math

from typing import List
from datetime import datetime

from pyanalysis.moment import moment
from pyanalysis.mysql import Conn
from pyghostbt.const import CONTRACT_TYPE_THIS_WEEK
from pyghostbt.const import CONTRACT_TYPE_NEXT_WEEK
from pyghostbt.const import CONTRACT_TYPE_QUARTER
from pyghostbt.const import SETTLE_MODE_BASIS
from pyghostbt.const import TRADE_TYPE_SPOT


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
    """Get the standard number value.

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
    """Get the real value of the standard number.

    Args:
        std_num: The number you want to reduction.

    Returns:
        The real value of the number.
    """
    return float(std_num) / 100000000


def interval_time_series(
        start_ts: int = 1199116800000,
        timezone: str = "Asia/Shanghai",
        interval: str = "1day",
):
    now_ts = moment.now().millisecond_timestamp
    flag_ts = start_ts
    while flag_ts < now_ts:
        yield flag_ts
        flag_ts += 24 * 60 * 60 * 1000


def backtest_time_series(
        backtest_id: str = "",
        trade_type: str = TRADE_TYPE_SPOT,
        db_name: str = "",
):
    conn = Conn(db_name)
    return conn.query_range(
        sql="SELECT wait_start_timestamp FROM {}_instance_backtest"
            " WHERE backtest_id = ? AND wait_start_timestamp != 0"
            " GROUP BY wait_start_timestamp ORDER BY wait_start_timestamp".format(trade_type),
        args=(backtest_id,),
    )


# pdr is short for position_dilution_ratio
def get_amount_and_pdr(
        asset_total: float = None,
        max_rel_loss_ratio: float = None,
        position: float = None,
        unit_amount: int = 1,
        slippage: float = None,
        open_price: int = None,
        liquidate_price: int = None,
        open_times: int = 3,
        fee_rate: float = -0.0005,
        scale: float = 1.0,
        settle_mode: int = SETTLE_MODE_BASIS,
) -> (float, float):
    """
    Get the first open amount.
    The open amount is a complicated calculating process. This func calculate it for worst situation. Why complicated?
    1. asset_total包含了fee + 保证金。其中fee是损失，所以asset_total并不能当做净值计算open_amount。
    2. 开仓平仓会有滑点，滑点会带来fee的变动，以及open_amount的变动。

    故此方法假设，此次交易以最差的情况止损。并在开仓，平仓都有滑点的情况下完成交易。

    Args:
        asset_total: The total asset of the pair
        max_rel_loss_ratio: The max loss relative 1 position, defined in param.
        position: The position want to open.
        unit_amount: The contract unit amount, may used in future, default is none.
        slippage: The slippage must be negative.
        open_price: The avg_price of open orders.
        liquidate_price: The avg_price of worst loss liquidate orders.
        open_times: The times to divide.
        fee_rate: The fee rate
        scale: The next open_amount/this open_amount, default is 1.
        settle_mode: settle with which currency.
    Returns:
        amount array of each open times.
    """
    if settle_mode == SETTLE_MODE_BASIS:
        return __amount_and_pdr_basis(
            asset_total=asset_total,
            max_rel_loss_ratio=max_rel_loss_ratio,
            position=position,
            unit_amount=unit_amount,
            slippage=slippage,
            open_price=open_price,
            liquidate_price=liquidate_price,
            open_times=open_times,
            fee_rate=fee_rate,
            scale=scale,
        )

    return __amount_and_pdr_counter(
        asset_total=asset_total,
        max_rel_loss_ratio=max_rel_loss_ratio,
        position=position,
        unit_amount=unit_amount,
        slippage=slippage,
        open_price=open_price,
        liquidate_price=liquidate_price,
        open_times=open_times,
        fee_rate=fee_rate,
        scale=scale,
    )


# entrance
# 以basis为基准的计价。
def __amount_and_pdr_basis(
        asset_total: float = None,
        max_rel_loss_ratio: float = None,
        position: float = None,
        unit_amount: int = None,
        slippage: float = None,
        open_price: int = None,
        liquidate_price: int = None,
        open_times: int = None,
        fee_rate: float = None,
        scale: float = None,
) -> (float, float):
    real_open_slippage = real_number(open_price) * abs(slippage)
    # open long
    if liquidate_price < open_price:
        real_open_price = real_number(open_price) + real_open_slippage
        real_loss_price = real_number(liquidate_price) + real_open_slippage
        real_loss_price *= (1 - abs(slippage))
    # open short
    else:
        real_open_price = real_number(open_price) - real_open_slippage
        real_loss_price = real_number(liquidate_price) - real_open_slippage
        real_loss_price *= (1 + abs(slippage))

    # 以最小价格计算开仓数量
    real_worst_price = min([real_open_price, real_loss_price])
    # 粗略的开仓张数
    open_amount = asset_total * position * real_worst_price / unit_amount
    # 计算出粗略的费用手续费。
    max_open_fee = open_amount * unit_amount * -abs(fee_rate) / real_open_price
    max_liquidate_fee = open_amount * unit_amount * -abs(fee_rate) / real_loss_price
    # 剔除手续费之后的资产净值。
    asset_net = asset_total + max_open_fee + max_liquidate_fee
    # 精准计算开仓数量。
    open_amount = asset_net * position * real_worst_price / unit_amount

    amounts: List[float] = []
    total_amount = 0
    total_scale = scale * open_times
    # 等比数列计算公式。
    if scale != 1.0:
        total_scale = (1 - math.pow(scale, open_times)) / (1 - scale)

    for i in range(open_times):
        amount = int(open_amount * math.pow(scale, i) / total_scale)
        total_amount += amount
        amounts.append(amount)

    real_loss_asset = abs(total_amount * unit_amount * (real_loss_price - real_open_price))
    real_loss_asset /= real_open_price
    real_loss_asset /= real_loss_price

    max_loss_asset = abs(max_rel_loss_ratio * asset_net * position)  # 相对于设置的position亏损最大资产值
    if real_loss_asset > max_loss_asset:  # 超过了最大可以亏的金额时，要缩小头寸规模。
        pdr = max_loss_asset / real_loss_asset
        return [int(pdr * a) for a in amounts][0], pdr

    return amounts[0], 1.0


# entrance done!
# 以counter为基准的计价。
def __amount_and_pdr_counter(
        asset_total: float = None,
        max_rel_loss_ratio: float = None,
        position: float = None,
        unit_amount: int = None,
        slippage: float = None,
        open_price: int = None,
        liquidate_price: int = None,
        open_times: int = None,
        fee_rate: float = None,
        scale: float = None,
) -> (float, float):
    real_open_slippage = real_number(open_price) * abs(slippage)
    # 做多时的情况。
    if liquidate_price < open_price:
        real_open_price = real_number(open_price) + real_open_slippage
        # 止损时要考虑open时的滑点，造成了平仓价格也收到影响。
        real_loss_price = real_number(liquidate_price) + real_open_slippage
        # 加入平仓时的滑点。
        real_loss_price *= (1 - abs(slippage))
    # 做空时的情况。
    else:
        real_open_price = real_number(open_price) - real_open_slippage
        # 止损时要考虑open时的滑点，造成了平仓价格也收到影响。
        real_loss_price = real_number(liquidate_price) - real_open_slippage
        # 加入平仓时的滑点。
        real_loss_price *= (1 + abs(slippage))

    # 粗略的开仓张数
    open_amount = asset_total * position / real_open_price
    # 计算出粗略的费用手续费。
    open_fee = open_amount * real_open_price * -abs(fee_rate)
    liquidate_fee = open_amount * real_loss_price * -abs(fee_rate)

    # 剔除手续费之后的资产净值。
    asset_net = asset_total + open_fee + liquidate_fee
    # 精准计算开仓数量。
    open_amount = asset_net * position / real_open_price

    amounts: List[float] = []
    total_amount = 0
    total_scale = scale * open_times
    # 等比数列计算公式。
    if scale != 1.0:
        total_scale = (1 - math.pow(scale, open_times)) / (1 - scale)
    for i in range(open_times):
        amount = standard_number(open_amount * math.pow(scale, i) / total_scale)
        total_amount += amount
        amounts.append(amount)

    real_loss_asset = abs(real_number(total_amount) * (real_loss_price - real_open_price))
    max_loss_asset = abs(max_rel_loss_ratio * asset_net * position)  # 相对于设置的position亏损最大资产值

    # 当unit_amount取非1的数时，其实相当于交易所想让用户把下单数量取整，所以这块不做标准处理了。
    if unit_amount > 1.0 or unit_amount < 1.0:
        # 超过了最大可以亏的金额时，要缩小头寸规模。
        if real_loss_asset > max_loss_asset:
            pdr = max_loss_asset / real_loss_asset
            return [int(pdr * real_number(a) * real_open_price / unit_amount) for a in amounts][0], pdr
        else:
            return int(real_number(amounts[0]) * real_open_price / unit_amount), 1.0
    else:
        # 超过了最大可以亏的金额时，要缩小头寸规模。
        if real_loss_asset > max_loss_asset:
            pdr = max_loss_asset / real_loss_asset
            return [int(pdr * a) for a in amounts][0], pdr
        else:
            return amounts[0], 1.0


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
