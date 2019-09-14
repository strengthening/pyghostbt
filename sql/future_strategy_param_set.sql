CREATE TABLE `future_strategy_param_set` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `instance_id` int(11) NOT NULL COMMENT 'instance id',
  `param_name` varchar(50) NOT NULL,
  `param_type` varchar(20) NOT NULL COMMENT 'int64/float/string',
  `param_value` text,
  `create_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `update_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `instance_id` (`instance_id`, `param_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
