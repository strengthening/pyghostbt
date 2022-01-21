ALTER TABLE `ghost_etl`.`factor_metadata`
ADD COLUMN `contract_type` varchar(20) NOT NULL DEFAULT 'none' COMMENT 'The factor contract type' AFTER `trade_type`;


