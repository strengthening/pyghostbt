CREATE TABLE `future_indices_strategy` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `instance_id` int(11) NOT NULL COMMENT 'instance id',
  `indices_name` varchar(50) NOT NULL,
  `indices_type` varchar(20) NOT NULL COMMENT 'int64/float/string',
  `indices_value` text,
  `create_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `update_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `instance_id` (`instance_id`, `indices_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
