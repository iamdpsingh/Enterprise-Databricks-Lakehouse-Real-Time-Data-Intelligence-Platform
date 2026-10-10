'use server';

import { DBSQLClient } from '@databricks/sql';

const DATABRICKS_HOST = process.env.DATABRICKS_HOST;
const DATABRICKS_HTTP_PATH = process.env.NEXT_PUBLIC_DATABRICKS_SQL_HTTP_PATH;
const DATABRICKS_TOKEN = process.env.NEXT_PUBLIC_DATABRICKS_API_TOKEN;

async function executeQuery(query: string) {
  if (!DATABRICKS_HOST || !DATABRICKS_HTTP_PATH || !DATABRICKS_TOKEN) {
    console.warn("Databricks credentials missing in .env. Returning null for query.");
    return null;
  }

  const client = new DBSQLClient();
  try {
    await client.connect({
      host: DATABRICKS_HOST.replace('https://', '').replace(/\/$/, ''),
      path: DATABRICKS_HTTP_PATH,
      token: DATABRICKS_TOKEN,
    });

    const session = await client.openSession();
    const queryOperation = await session.executeStatement(query, {
      runAsync: true,
    });
    const result = await queryOperation.fetchAll();
    
    await session.close();
    await client.close();
    
    return result;
  } catch (error) {
    console.error("Databricks SQL Execution Error:", error);
    return null;
  }
}

export async function getEthereumMetrics() {
  const data = await executeQuery('SELECT COUNT(*) as txCount, AVG(CAST(gas AS DOUBLE)) as avgGas, SUM(CAST(value AS DOUBLE)) as totalTransfers FROM prod_catalog.ethereum.bronze');
  if (!data || data.length === 0 || !data[0].txCount) return { totalTransfers: '0 ETH', avgGas: '0', txCount: '0' };
  
  return {
    totalTransfers: `${(Number(data[0].totalTransfers) / 1e18).toFixed(2)} ETH`,
    avgGas: Math.round(Number(data[0].avgGas)).toString(),
    txCount: data[0].txCount.toString()
  };
}

export async function getGithubMetrics() {
  const data = await executeQuery('SELECT COUNT(*) as events, COUNT(DISTINCT repo_name) as uniqueRepos, SUM(CASE WHEN type = "PushEvent" THEN 1 ELSE 0 END) as pushEvents FROM prod_catalog.github.bronze');
  if (!data || data.length === 0 || !data[0].events) return { events: '0', uniqueRepos: '0', pushEvents: '0' };
  
  return {
    events: data[0].events.toString(),
    uniqueRepos: data[0].uniqueRepos.toString(),
    pushEvents: data[0].pushEvents.toString()
  };
}

export async function getOvertureMetrics() {
  const data = await executeQuery('SELECT COUNT(*) as pois, COUNT(DISTINCT category) as categories, COUNT(DISTINCT ROUND(latitude, 0)) as regions FROM prod_catalog.overture.bronze');
  if (!data || data.length === 0 || !data[0].pois) return { pois: '0', categories: '0', regions: '0' };
  
  return {
    pois: data[0].pois.toString(),
    categories: data[0].categories.toString(),
    regions: data[0].regions.toString()
  };
}

export async function getQuarantineMetrics() {
  const data = await executeQuery('SELECT _quarantine_failed_rules, _ingested_at, id FROM prod_catalog.quality.quarantine ORDER BY _ingested_at DESC LIMIT 10');
  
  if (!data || data.length === 0) return [];
  
  return data.map((row: any) => ({
    _quarantine_reason: row._quarantine_failed_rules?.toString() || 'Unknown Failure',
    _quarantine_timestamp: row._ingested_at?.toString() || new Date().toISOString(),
    order_id: row.id?.toString() || 'N/A',
    customer_id: 'Quarantined'
  }));
}

export async function getPlatformMetrics() {
  const data = await executeQuery(`
    SELECT 
      (SELECT COUNT(*) FROM prod_catalog.ethereum.bronze) as eth_count,
      (SELECT COUNT(*) FROM prod_catalog.github.bronze) as gh_count,
      (SELECT COUNT(*) FROM prod_catalog.overture.bronze) as ov_count,
      (SELECT MAX(created_at) FROM prod_catalog.github.bronze) as latest_gh
  `);
  
  if (!data || data.length === 0) {
    return { totalRecords: 'N/A', latestSync: 'N/A', ethRows: 'N/A', ghRows: 'N/A', ovRows: 'N/A' };
  }
  
  const ethCount = Number(data[0].eth_count || 0);
  const ghCount = Number(data[0].gh_count || 0);
  const ovCount = Number(data[0].ov_count || 0);
  const total = ethCount + ghCount + ovCount;

  return {
    totalRecords: total.toString(),
    latestSync: data[0].latest_gh ? new Date(data[0].latest_gh).toLocaleTimeString() : 'Awaiting Data...',
    ethRows: ethCount.toString(),
    ghRows: ghCount.toString(),
    ovRows: ovCount.toString()
  };
}
