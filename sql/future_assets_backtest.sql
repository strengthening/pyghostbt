CREATE TABLE `future_assets_backtest` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `symbol` varchar(30) NOT NULL,
  `exchange` varchar(20) NOT NULL,
  `total_asset` decimal(20,8) COMMENT '资金账户+余币宝+期货账户开仓订单盈利情况都算成0的情况（total_avail_balance + realized_pnl）',
  `anchor_asset` decimal(20,8) COMMENT '资金账户+余币宝+期货账户开仓订单盈利情况都算成最大损失的情况（total_avail_balance + realized_pnl + future_max_loss_asset）',
  `future_total_asset` decimal(20,8) COMMENT '期货账户开仓订单盈利情况都算成0的情况（total_avail_balance + realized_pnl）',
  `future_anchor_asset` decimal(20,8) COMMENT '期货账户开仓订单盈利情况都算成最大损失的情况（total_avail_balance + realized_pnl + future_max_loss_asset）',
  `future_max_margin_asset` decimal(20,8) COMMENT '期货账户已经最大占用的保证金',
  `future_max_loss_asset` decimal(20,8) COMMENT '期货账户损失资金上线，滑点+手续费+最大损失金额',
  `total_position` decimal(2,4) COMMENT '账户总份数',
  `future_position` decimal(2,4) COMMENT '期货账户定期补全的position',
  `future_limit_position` decimal(2,4) COMMENT '期货账户限制的position',
  `future_opened_position` decimal(2,4) COMMENT '期货账户开仓的position',
  `snapshot_timestamp` bigint(13) NOT NULL COMMENT 'the snap timestamp',
  `snapshot_datetime` datetime NOT NULL COMMENT 'the snap datetime',
  `create_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `update_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `symbol` (`symbol`, `exchange`, `snap_timestamp`),
  KEY `snap_timestamp` (`snap_timestamp`),
  KEY `snapshot_datetime` (`snapshot_datetime`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

