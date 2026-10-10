-- Unity Catalog DDL for 4 Global Datasets
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

-- Reddit Pushshift
CREATE SCHEMA IF NOT EXISTS reddit;
CREATE TABLE IF NOT EXISTS reddit.bronze (id STRING, author STRING, selftext STRING, created_utc BIGINT, subreddit STRING, score INT, num_comments INT);
CREATE TABLE IF NOT EXISTS reddit.silver (id STRING, author STRING, clean_text STRING, created_utc BIGINT, subreddit STRING, score INT, num_comments INT, is_current BOOLEAN, updated_at TIMESTAMP, valid_from TIMESTAMP, valid_to TIMESTAMP);
CREATE TABLE IF NOT EXISTS reddit.gold (subreddit STRING, post_date DATE, total_posts BIGINT, avg_score DOUBLE, total_comments BIGINT);

-- Quarantine
CREATE SCHEMA IF NOT EXISTS quality;
CREATE TABLE IF NOT EXISTS quality.quarantine (dataset STRING, record STRING, _quarantine_failed_rules STRING);
