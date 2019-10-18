# 文件及其解释


### 工具
- kline.py k线数据
- indices.py 技术指标 和 instance相关
- params.py 策略参数 和 instance相关
- asset.py 资金管理或者仓位管理。


### 应用
- strategy.py 策略逻辑，从配置到生成instance，持久化instance。
- backtest.py 回测逻辑
- portfolio.py 复盘及评估策略


### 需要调研的包
jsonschema
pyfolio
