ALTER TABLE `swap_instance_strategy`
ADD COLUMN `unit_amount` int(11) DEFAULT 1 AFTER `strategy`;

ALTER TABLE `swap_order_strategy`
ADD COLUMN `unit_amount` int(11) NULL DEFAULT 1 AFTER `exchange`;

ALTER TABLE `swap_instance_backtest`
ADD COLUMN `unit_amount` int(11) DEFAULT 1 AFTER `strategy`;

ALTER TABLE `swap_order_backtest`
ADD COLUMN `unit_amount` int(11) NULL DEFAULT 1 AFTER `exchange`;
