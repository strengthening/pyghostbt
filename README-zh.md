# pyghostbt

README: [English](https://github.com/strengthening/pyghostbt/blob/master/README.md) | [中文](https://github.com/strengthening/pyghostbt/blob/master/README-zh.md)

Pyghostbt是一款开源回测框架，专注于程序化交易的中低频交易策略回测。甚至于在生产环境中直接产生交易逻辑。    
这不是事件驱动的回测框架。本框架仅仅在一段时间内产生交易逻辑。

## 优劣势
非事件驱动回测，有优势同样也有劣势。

- 优势
    - 交易逻辑和交易执行可拆分。
- 劣势
    - 仅仅适用于中低频交易策略。
    
## 特性

- 一些常用的技术指标。
- 中低频交易的回测框架。
- 在生产环境中直接产生交易逻辑。

## 待完成

- 支持现货交易的回测。
- 支持杠杆交易的回测。
- 支持永续合约的回测。

## 注意

- 仅在backtest时写入数据。
- 仅在strategy时读入数据。

## 单元测试

python3 -m unittest test/future/log.py

## 许可协议

项目使用 [New BSD 许可协议](./LICENSE)
