CREATE TABLE `future_asset_backtest` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `exchange` varchar(20) NOT NULL,
  `settle_mode` tinyint(4) NOT NULL DEFAULT '1' COMMENT 'the settle mode, 1: basis currency, 2: counter currency',
  `settle_currency` varchar(20) NOT NULL DEFAULT '' COMMENT 'the settle currency',
  `backtest_id` varchar(32) NOT NULL COMMENT '单次回测的标识',
  `asset_total` decimal(20,8) COMMENT '总账户资产数量，资金账户+余币宝+期货账户开仓订单盈利情况都算成0的情况（total_avail_balance + realized_pnl）',
  `asset_sub` decimal(20,8) COMMENT '子账户资产数量，期货账户开仓订单盈利情况都算成0的情况（total_avail_balance + realized_pnl）',
  `asset_freeze` decimal(20,8) COMMENT '子账户冻结数量，期货账户当前冻结的资产,主要用于保证金/支付损失/支付手续费',
  `position_total` tinyint(4) COMMENT '总账户总仓位',
  `position_sub` tinyint(4) COMMENT '期货账户中的仓位',
  `position_freeze` decimal(11,4) COMMENT '期货账户中冻结的仓位',
  `timestamp` bigint(13) NOT NULL COMMENT '计算的时间戳',
  `datetime` datetime NOT NULL COMMENT '计算的日期',
  `create_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `update_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `exchange` (`exchange`, `settle_mode`, `settle_currency`, `timestamp`, `backtest_id`),
  KEY `timestamp` (`timestamp`),
  KEY `datetime` (`datetime`),
  KEY `backtest_id` (`backtest_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
