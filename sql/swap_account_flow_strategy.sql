CREATE TABLE `swap_account_flow_strategy` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `symbol` varchar(30) NOT NULL,
  `exchange` varchar(20) NOT NULL,
  `settle_mode` tinyint(4) NOT NULL DEFAULT '0' COMMENT '1: basis currency, 2: counter currency',
  `settle_currency` varchar(20) NOT NULL DEFAULT '' COMMENT 'the settle currency',
  `subject` varchar(30) NOT NULL COMMENT 'injection/dividend/freeze/unfreeze/income/transaction_fee/adjustment/transfer',
  `amount` bigint(20) NOT NULL COMMENT 'the real amount * 100000000',
  `position` decimal(11,4) NOT NULL COMMENT 'the subject used position',
  `timestamp` bigint(13) NOT NULL COMMENT 'timestamp',
  `datetime` datetime NOT NULL COMMENT 'datetime',
  `create_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `update_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `symbol` (`symbol`,`exchange`,`settle_mode`,`settle_currency`,`subject`,`timestamp`),
  KEY `exchange` (`exchange`,`settle_mode`,`settle_currency`,`timestamp`,`subject`),
  KEY `timestamp` (`timestamp`),
  KEY `datetime` (`datetime`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
