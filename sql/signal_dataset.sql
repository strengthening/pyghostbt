CREATE TABLE `signal_dataset` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `signal_id` int(11) NOT NULL COMMENT 'The signal id, defined in metadata',
  `start_timestamp` bigint(13) NOT NULL COMMENT 'The signal start happened timestamp',
  `start_datetime` datetime COMMENT 'The signal start happened datetime',
  `finish_timestamp` bigint(13) NOT NULL COMMENT 'The signal finished timestamp',
  `finish_datetime` datetime COMMENT 'The signal finished datetime',
  `create_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `update_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `signal_id` (`signal_id`, `start_timestamp`),
  KEY `start_timestamp` (`start_timestamp`),
  KEY `finish_timestamp` (`finish_timestamp`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
