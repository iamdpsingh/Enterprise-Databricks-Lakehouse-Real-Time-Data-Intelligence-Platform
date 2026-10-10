-- Unity Catalog DDL for 3 Global Datasets
CREATE CATALOG IF NOT EXISTS prod_catalog;
USE CATALOG prod_catalog;

-- Ethereum Web3
CREATE SCHEMA IF NOT EXISTS ethereum;
CREATE TABLE IF NOT EXISTS ethereum.bronze (hash STRING, gas STRING, value STRING, block_timestamp TIMESTAMP);
CREATE TABLE IF NOT EXISTS ethereum.silver (hash STRING, gas_long BIGINT, value_long BIGINT, block_timestamp TIMESTAMP);
CREATE TABLE IF NOT EXISTS ethereum.gold (block_date DATE, to_address STRING, total_eth_transferred BIGINT, avg_gas_used BIGINT, tx_count BIGINT);

-- GitHub Archive
CREATE SCHEMA IF NOT EXISTS github;
CREATE TABLE IF NOT EXISTS github.bronze (id STRING, type STRING, repo_name STRING, created_at TIMESTAMP);
CREATE TABLE IF NOT EXISTS github.silver (id STRING, type STRING, repo_name STRING, created_at TIMESTAMP);
CREATE TABLE IF NOT EXISTS github.gold (repo_name STRING, event_date DATE, type STRING, event_count BIGINT);

-- Overture Maps
CREATE SCHEMA IF NOT EXISTS overture;
CREATE TABLE IF NOT EXISTS overture.bronze (id STRING, category STRING, lat DOUBLE, lon DOUBLE);
CREATE TABLE IF NOT EXISTS overture.silver (id STRING, category STRING, lat DOUBLE, lon DOUBLE);
CREATE TABLE IF NOT EXISTS overture.gold (category STRING, poi_count BIGINT);


-- Quarantine
CREATE SCHEMA IF NOT EXISTS quality;
CREATE TABLE IF NOT EXISTS quality.quarantine (dataset STRING, record STRING, _quarantine_failed_rules STRING);
