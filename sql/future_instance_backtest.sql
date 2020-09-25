CREATE TABLE `future_instance_backtest` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `symbol` varchar(30) NOT NULL,
  `exchange` varchar(20) NOT NULL,
  `contract_type` varchar(20) NOT NULL,
  `backtest_id` varchar(32) NOT NULL COMMENT 'backtest unique id',
  `strategy` varchar(20) NOT NULL,
  `unit_amount` int(11) NOT NULL DEFAULT '10',
  `lever` int(11) NOT NULL DEFAULT '10',
  `status` tinyint(1) NOT NULL COMMENT '0: waiting, 1: opening, 2: liquidating, 3: finished, 9: error',
  `interval` varchar(20) NOT NULL DEFAULT '1day' COMMENT 'the strategy logic generate interval: 1min/1hour/4hour/1day/1week',

-- some columns about the asset
  `asset_total` decimal(20,8) COMMENT 'the total account asset for future',
  `asset_pnl` decimal(20,8) COMMENT 'the total pnl asset at the end',
  `asset_freeze` decimal(20,8) COMMENT 'the sub account freeze asset for this instance',

  `param_position` decimal(11,6) NOT NULL DEFAULT '0.0' COMMENT 'the strategy use account asset scale, sometime you do not want use full margined asset to open',
  `param_max_abs_loss_ratio` decimal(11,6) NOT NULL DEFAULT '0.0' COMMENT '',

  `wait_start_timestamp` bigint(13) NOT NULL COMMENT '等待开单开始时间戳',
  `wait_start_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '等待开单开始时间',
  `wait_finish_timestamp` bigint(13) NOT NULL DEFAULT '0' COMMENT '等待开单结束时间戳',
  `wait_finish_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '等待开单结束时间',

  `open_type` tinyint(1) NOT NULL DEFAULT '1' COMMENT '1: open_long, 2: open_short',
  `open_place_type` varchar(10) NOT NULL DEFAULT 't_taker' COMMENT 't_taker t_maker b_taker b_maker o_swap l_swap market',
  `open_times` tinyint(1) NOT NULL DEFAULT '1' COMMENT '开仓的次数，1~9',
  `open_fee` decimal(20,8) COMMENT '开仓费用',
  `open_start_timestamp` bigint(13) COMMENT '开仓开始时间戳',
  `open_start_datetime` datetime COMMENT '开仓开始时间',
  `open_finish_timestamp` bigint(13) COMMENT '开仓结束时间戳',
  `open_finish_datetime` datetime COMMENT '开仓结束时间',
  `open_expired_timestamp` bigint(13) COMMENT '开仓超时时间戳',
  `open_expired_datetime` datetime COMMENT '开仓超时时间',

  `swap_times` tinyint(1) NOT NULL DEFAULT '0' COMMENT '1~9',
  `swap_fee` decimal(20,8) COMMENT '换仓手续费',
  `swap_asset_pnl` decimal(20,8) COMMENT '换仓损益资产',

  `liquidate_type` tinyint(1) NOT NULL DEFAULT '3' COMMENT '3: liquidate_long, 4: liquidate_short',
  `liquidate_place_type` varchar(10) NOT NULL DEFAULT 'b_taker' COMMENT 't_taker t_maker b_taker b_maker o_swap l_swap market',
  `liquidate_times` tinyint(1) NOT NULL DEFAULT '1' COMMENT '平仓的次数，1~9',
  `liquidate_fee` decimal(20,8) COMMENT '- anchored_asset*position*rate',
  `liquidate_start_timestamp` bigint(13) COMMENT '平仓开始时间戳',
  `liquidate_start_datetime` datetime COMMENT '平仓开始时间',
  `liquidate_finish_timestamp` bigint(13) COMMENT '平仓结束时间戳',
  `liquidate_finish_datetime` datetime COMMENT '平仓结束时间',

  `create_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `update_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `symbol` (`symbol`, `exchange`, `contract_type`, `strategy`, `wait_start_timestamp`, `backtest_id`),
  KEY `open_start_timestamp` (`open_start_timestamp`, `status`),
  KEY `wait_start_timestamp` (`wait_start_timestamp`),
  KEY `liquidate_finish_timestamp` (`liquidate_finish_timestamp`),
  KEY `backtest_id` (`backtest_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
