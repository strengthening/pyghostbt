CREATE TABLE `future_assets_backtest` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `symbol` varchar(30) NOT NULL,
  `exchange` varchar(20) NOT NULL,
  `total_asset` decimal(20,8) COMMENT 'the future account total asset, when the opening instances set to 0',
  `anchor_asset` decimal(20,8) COMMENT 'the future account anchor asset, when the opening instances set to max loss',
  `snapshot_timestamp` bigint(13) NOT NULL COMMENT 'the snap timestamp',
  `snapshot_datetime` datetime NOT NULL COMMENT 'the snap datetime',
  `create_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `update_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `symbol` (`symbol`, `exchange`, `snap_timestamp`),
  KEY `snap_timestamp` (`snap_timestamp`),
  KEY `snapshot_datetime` (`snapshot_datetime`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
