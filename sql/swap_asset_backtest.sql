CREATE TABLE `swap_asset_backtest` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `exchange` varchar(20) NOT NULL,
  `settle_mode` tinyint(4) NOT NULL DEFAULT '1' COMMENT '1: basis currency, 2: counter currency',
  `settle_currency` varchar(20) NOT NULL DEFAULT '' COMMENT 'the settle currency',
  `backtest_id` varchar(32) NOT NULL COMMENT '单次回测的标识',
  `asset_total` decimal(20,8) COMMENT '锚定的总资产',
  `asset_sub` decimal(20,8) COMMENT '永续合约子账户的资产',
  `asset_freeze` decimal(20,8) COMMENT '永续合约子账户冻结数量，期货账户当前冻结的资产，主要用于保证金/支付损失/支付手续费',
  `position_total` tinyint(4) COMMENT '总仓位数',
  `position_sub` tinyint(4) COMMENT '期货账户中的总仓位',
  `position_freeze` decimal(11,4) COMMENT '期货账户中冻结的仓位',
  `timestamp` bigint(13) NOT NULL COMMENT '计算的时间戳',
  `datetime` datetime NOT NULL COMMENT '计算的日期',
  `create_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `update_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `exchange` (`exchange`, `settle_mode`, `settle_currency`, `timestamp`, `backtest_id`),
  KEY `timestamp` (`timestamp`),
  KEY `datetime` (`datetime`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
