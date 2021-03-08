CREATE TABLE `factor_metadata` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `symbol` varchar(20) NOT NULL COMMENT 'The factor symbol',
  `trade_type` varchar(20) NOT NULL COMMENT 'The factor trade type',
  `interval` varchar(10) NOT NULL DEFAULT '1day' COMMENT 'The factor interval',
  `factor_name` varchar(30) NOT NULL COMMENT 'The factor name',
  `factor_desc` text COMMENT 'The factor desc, include factor raw data, factor calculation formula',
  `create_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `update_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `symbol` (`symbol`,`trade_type`,`interval`,`factor_name`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
