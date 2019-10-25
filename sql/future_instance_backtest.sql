CREATE TABLE `future_instance_backtest` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `symbol` varchar(30) NOT NULL,
  `exchange` varchar(20) NOT NULL,
  `contract_type` varchar(20) NOT NULL,
  `backtest_id` varchar(32) NOT NULL COMMENT 'backtest unique id',
  `strategy` varchar(20) NOT NULL,
  `unit_amount` int(11) NOT NULL,
  `lever` int(11) NOT NULL,
  `status` tinyint(1) NOT NULL COMMENT '0: wait_open, 1: opening, 2: wait_liquidate, 3: liquidating, 4: finished, 9: error',
  `interval` varchar(20) NOT NULL COMMENT 'the strategy logic generate interval: 1min/1hour/4hour/1day/1week',
  `start_timestamp` bigint(13) NOT NULL,
  `start_datetime` datetime NOT NULL,
  `finish_timestamp` bigint(13) NOT NULL,
  `finish_datetime` datetime NOT NULL,

-- some columns about the asset
  `total_asset` decimal(20,8) COMMENT 'the total asset for future',
  `freeze_asset` decimal(20,8) COMMENT 'the freeze asset for this instance',

  `open_type` tinyint(1) NOT NULL COMMENT '1: open_long, 2: open_short',
  `open_place_type` varchar(10) NOT NULL COMMENT 'taker maker',
  `open_skill` varchar(20) NOT NULL COMMENT 'ratio diff none',
  `open_times` tinyint(1) NOT NULL COMMENT '1~9',
  `open_swap` tinyint(1) NOT NULL,
  `open_fee` decimal(20,8) COMMENT '开仓费用',
  `open_timestamp` bigint(13) COMMENT '首次开仓时间戳',
  `open_datetime` datetime COMMENT '首次开仓时间',

  `liquidate_type` tinyint(1) NOT NULL COMMENT '3: liquidate_long, 4: liquidate_short',
  `liquidate_place_type` varchar(10) NOT NULL COMMENT 'taker maker',
  `liquidate_skill` varchar(20) NOT NULL COMMENT 'ratio diff none',
  `liquidate_times` tinyint(1) NOT NULL COMMENT '1~9',
  `liquidate_swap` tinyint(1) NOT NULL,
  `liquidate_fee` decimal(20,8) COMMENT '- anchored_asset*position*rate',
  `liquidate_timestamp` bigint(13) COMMENT '首次平仓时间戳',
  `liquidate_datetime` datetime COMMENT '首次平仓时间',

  `param_position` decimal(2,6) NOT NULL COMMENT 'the strategy use account asset scale, sometime you do not want use full margined asset to open',
  `param_max_abs_loss` decimal(2,6) NOT NULL COMMENT '',

  `create_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `update_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `symbol` (`symbol`, `exchange`, `contract_type`, `strategy`, `interval`, `start_timestamp`),
  KEY `open_timestamp` (`open_timestamp`, `status`),
  KEY `start_timestamp` (`start_timestamp`),
  KEY `liquidate_timestamp` (`liquidate_timestamp`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
