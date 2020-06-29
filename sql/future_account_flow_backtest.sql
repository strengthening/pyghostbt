CREATE TABLE `future_account_flow_backtest` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `symbol` varchar(30) NOT NULL,
  `exchange` varchar(20) NOT NULL,
  `settle_mode` tinyint(4) NOT NULL DEFAULT '1' COMMENT '1: basis currency, 2: counter currency',
  `backtest_id` varchar(32) NOT NULL COMMENT 'backtest unique id',
  `subject` varchar(30) NOT NULL COMMENT 'injection/dividend/freeze/unfreeze/income/transaction_fee/adjustment/transfer',
  `amount` bigint(20) NOT NULL COMMENT 'the real amount * 100000000',
  `position` decimal(11,4) NOT NULL COMMENT 'the subject used position',
  `timestamp` bigint(13) NOT NULL COMMENT 'timestamp',
  `datetime` datetime NOT NULL COMMENT 'datetime',
  `create_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `update_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `symbol` (`symbol`, `exchange`, `subject`, `timestamp`, `backtest_id`),
  KEY `timestamp` (`timestamp`),
  KEY `datetime` (`datetime`),
  KEY `backtest_id` (`backtest_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
