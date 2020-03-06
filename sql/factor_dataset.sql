CREATE TABLE `factor_dataset` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `factor_id` int(11) NOT NULL COMMENT 'The factor id, defined in metadata',
  `factor_value` decimal(20, 8) DEFAULT '0.00000000' COMMENT 'The factor data float value',
  `timestamp` bigint(13) NOT NULL COMMENT 'The factor value at that timestamp',
  `date` datetime COMMENT 'value in date',
  `create_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `update_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `factor_id` (`factor_id`, `timestamp`),
  KEY `timestamp` (`timestamp`),
  KEY `date` (`date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
