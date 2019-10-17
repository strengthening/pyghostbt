CREATE TABLE `future_backtest_indices` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `symbol` varchar(30) NOT NULL,
  `exchange` varchar(20) NOT NULL,
  `contract_type` varchar(20) NOT NULL,
  `contract_name` varchar(20),
  `indices_name` varchar(50) NOT NULL,
  `indices_type` varchar(20) NOT NULL,
  `indices_value` text,
  `interval` varchar(20) NOT NULL COMMENT ''The indices interval: 1min/15min/1h/4h/1day/1week'',
  `start_timestamp` bigint(13) NOT NULL COMMENT ''The indices start timestamp'',
  `start_date` datetime COMMENT ''The indices start date'',
  `finish_timestamp` bigint(13) NOT NULL COMMENT ''The indices finish timestamp'',
  `finish_date` datetime COMMENT ''The indices finish date'',
  `due_timestamp` bigint(13) COMMENT ''The contract due timestamp'',
  `due_date` datetime COMMENT ''The contract due date'',
  `create_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `update_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `symbol` (`symbol`, `exchange`, `contract_type`, `indices_name`, `timestamp`),
  KEY `start_timestamp` (`start_timestamp`),
  KEY `start_date` (`start_date`),
  KEY `due_timestamp` (`due_timestamp`),
  KEY `due_date` (`due_date`),
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
