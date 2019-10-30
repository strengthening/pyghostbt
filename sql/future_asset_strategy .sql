CREATE TABLE `future_asset_strategy` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `symbol` varchar(30) NOT NULL,
  `exchange` varchar(20) NOT NULL,
  `total_account_asset` decimal(20,8) COMMENT '资金账户+余币宝+期货账户开仓订单盈利情况都算成0的情况（total_avail_balance + realized_pnl）',
  `future_account_asset` decimal(20,8) COMMENT '期货账户开仓订单盈利情况都算成0的情况（total_avail_balance + realized_pnl）',
  `future_freeze_asset` decimal(20,8) COMMENT '期货账户当前冻结的资产,主要用于保证金/支付损失/支付手续费',
  `total_account_position` tinyint(4) COMMENT '总账户总仓位',
  `future_account_position` tinyint(4) COMMENT '期货账户中的仓位',
  `future_freeze_position` decimal(4,4) COMMENT '期货账户中冻结的仓位',
  `timestamp` bigint(13) NOT NULL COMMENT '计算的时间戳',
  `datetime` datetime NOT NULL COMMENT '计算的日期',
  `create_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `update_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `symbol` (`symbol`, `exchange`, `timestamp`),
  KEY `timestamp` (`timestamp`),
  KEY `datetime` (`datetime`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
