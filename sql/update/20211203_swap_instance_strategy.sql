ALTER TABLE `swap_order_strategy`
MODIFY COLUMN `unit_amount` decimal(11, 8) NULL DEFAULT 1 AFTER `exchange`;

ALTER TABLE `swap_instance_strategy`
MODIFY COLUMN `unit_amount` decimal(11, 8) NULL DEFAULT 1 AFTER `strategy`;

ALTER TABLE `future_order_strategy`
MODIFY COLUMN `unit_amount` decimal(11, 8) NOT NULL DEFAULT 10 AFTER `contract_type`;

ALTER TABLE `future_instance_strategy`
MODIFY COLUMN `unit_amount` decimal(11, 8) NOT NULL DEFAULT 10 AFTER `strategy`;



ALTER TABLE `swap_order_backtest`
MODIFY COLUMN `unit_amount` decimal(11, 8) NULL DEFAULT 1 AFTER `exchange`;

ALTER TABLE `swap_instance_backtest`
MODIFY COLUMN `unit_amount` decimal(11, 8) NULL DEFAULT 1 AFTER `strategy`;

ALTER TABLE `future_order_backtest`
MODIFY COLUMN `unit_amount` decimal(11, 8) NOT NULL DEFAULT 10 AFTER `contract_type`;

ALTER TABLE `future_instance_backtest`
MODIFY COLUMN `unit_amount` decimal(11, 8) NOT NULL DEFAULT 10 AFTER `strategy`;




