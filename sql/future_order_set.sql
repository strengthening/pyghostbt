CREATE TABLE `future_order_set` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `sid` varchar(16) NOT NULL COMMENT 'order sid id',
  `cid` varchar(16) NOT NULL,
  `type` tinyint(4) NOT NULL COMMENT '1:open_long, 2:open_short, 3: liquidate_long, 4: liquidate_short',
  `price` bigint(20) NOT NULL COMMENT 'unit: 0.00000001',
  `amount` int(11) NOT NULL,
  `avg_price` bigint(11) COMMENT 'unit: 0.00000001',
  `deal_amount` int(11),
  `status` tinyint(4),
  `place_type` tinyint(4),
  `lever` int(11),
  `fee` decimal(20,8),
  `symbol` varchar(20),
  `exchange` varchar(20),
  `contract_type` varchar(20),
  `contract_name` varchar(20),
  `action` int(4) COMMENT '0~9:open, 20:liquidate_switch, 40:open_switch , 100:liquidate'
) ENGINE=InnoDB DEFAULT CHARSET=utf8;