CREATE TABLE `future_backtest_orders` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `instance_id` int(11) NOT NULL COMMENT 'instance id',
  `sequence` tinyint(2) NOT NULL COMMENT 'order sid sequence',
  `purpose` varchar(30) NOT NULL COMMENT 'maker/taker/swapper',
  `type` tinyint(1) NOT NULL COMMENT '1:open_long, 2:open_short, 3: liquidate_long, 4: liquidate_short',
  `remote_order_id` varchar(50) DEFAULT '' COMMENT 'order sid sequence',
  `price` bigint(20) NOT NULL COMMENT 'unit: 0.00000001',
  `amount` int(11) NOT NULL COMMENT 'price*margined_asset/open_times/unit_amount',
  `avg_price` bigint(20) COMMENT 'unit: 0.00000001',
  `deal_amount` int(11),
  `status` tinyint(4),
  `place_type` tinyint(4),
  `lever` int(11) NOT NULL,
  `fee` decimal(20,8),
  `symbol` varchar(30) NOT NULL,
  `exchange` varchar(20) NOT NULL,
  `contract_type` varchar(20) NOT NULL,
  `contract_name` varchar(20) NOT NULL,
  `order_timestamp` bigint(13),
  `order_date` datetime,
  `due_timestamp` bigint(13),
  `due_date` datetime,
  `swap_timestamp`: bigint(13),
  `swap_date` datetime,
  `cancel_timestamp`: bigint(13),
  `cancel_date` datetime,
  `create_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `update_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `instance_id` (`instance_id`,`sequence`),
) ENGINE=InnoDB DEFAULT CHARSET=utf8;