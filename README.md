# pyghostbt

README: [English](https://github.com/strengthening/pyghostbt/blob/master/README.md) | [中文](https://github.com/strengthening/pyghostbt/blob/master/README-zh.md)

Pyghostbt is a open source framework for program trader to backtest the medium/low frequency trading strategy, even directly generate the trade logic in production env.    
It is not event driven backtesting framework. It just generate trade log in a interval times. It fit for the medium/low frequency trading strategy. 

## Pros and cons
The anti-event backtesting framework has pros and cons.

- Pros
    - transaction logic and transaction execution are detachable.
- Cons
    - only suitable for medium/low frequency trading strategy.

## Feature

- some common technology indicators.
- the backtest framework for medium/low frequency trade.
- the trade strategy generate on the production.

## Todos

- Support spot backtest.
- Support margin backtest.
- Support swap backtest.

## Notice

- Just write data into backtest tables.
- Just read data in strategy tables.

## Unittest
python3 -m unittest test/future/log.py

## License

The project use the [New BSD License](./LICENSE)
