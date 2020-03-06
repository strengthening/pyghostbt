CREATE TABLE `signal_metadata` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `symbol` varchar(20) NOT NULL COMMENT 'The signal symbol',
  `exchange` varchar(20) NOT NULL COMMENT 'The signal exchange',
  `trade_type` varchar(20) NOT NULL COMMENT 'The signal trade type',
  `contract_type` varchar(20) NOT NULL DEFAULT 'none' COMMENT 'The signal contract type, default none',
  `signal_name` varchar(30) NOT NULL COMMENT 'The signal name',
  `signal_desc` text COMMENT 'The signal desc, include signal raw data, signal calculation formula',
  `create_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `update_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `symbol` (`symbol`, `exchange`, `trade_type`, `contract_type`, `signal_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
