ALTER TABLE `ghost_etl`.`spot_order_backtest`
ADD COLUMN `unit_amount` decimal(11, 8) NULL DEFAULT 1 AFTER `exchange`;

ALTER TABLE `ghost_etl`.`spot_instance_backtest`
ADD COLUMN `unit_amount` decimal(11, 8) NULL DEFAULT 1 AFTER `strategy`;
