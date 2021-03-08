ALTER TABLE `ghost_etl`.`factor_metadata`
ADD COLUMN `interval` varchar(10) NOT NULL DEFAULT '1day' COMMENT 'The factor interval' AFTER `trade_type`;

ALTER TABLE `ghost_etl`.`factor_metadata`
DROP INDEX `symbol`,
ADD UNIQUE INDEX `symbol`(`symbol`, `trade_type`, `interval`, `factor_name`) USING BTREE;

