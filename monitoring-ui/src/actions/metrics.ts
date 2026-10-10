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
      host: DATABRICKS_HOST.replace('https://', ''),
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
  const data = await executeQuery('SELECT COUNT(*) as txCount, AVG(gas) as avgGas, SUM(value) as totalTransfers FROM prod_catalog.ethereum.gold_metrics');
  if (!data || data.length === 0) return { totalTransfers: 'N/A', avgGas: 'N/A', txCount: 'N/A' };
  
  return {
    totalTransfers: `${(data[0].totalTransfers / 1e18).toFixed(2)} ETH`,
    avgGas: Math.round(data[0].avgGas).toString(),
    txCount: data[0].txCount.toString()
  };
}

export async function getGithubMetrics() {
  const data = await executeQuery('SELECT COUNT(*) as events, COUNT(DISTINCT repo_id) as uniqueRepos, SUM(CASE WHEN type = "PushEvent" THEN 1 ELSE 0 END) as pushEvents FROM prod_catalog.github.gold_metrics');
  if (!data || data.length === 0) return { events: 'N/A', uniqueRepos: 'N/A', pushEvents: 'N/A' };
  
  return {
    events: data[0].events.toString(),
    uniqueRepos: data[0].uniqueRepos.toString(),
    pushEvents: data[0].pushEvents.toString()
  };
}

export async function getOvertureMetrics() {
  const data = await executeQuery('SELECT COUNT(*) as pois, COUNT(DISTINCT category) as categories, COUNT(DISTINCT region) as regions FROM prod_catalog.overture.gold_metrics');
  if (!data || data.length === 0) return { pois: 'N/A', categories: 'N/A', regions: 'N/A' };
  
  return {
    pois: data[0].pois.toString(),
    categories: data[0].categories.toString(),
    regions: data[0].regions.toString()
  };
}

export async function getRedditMetrics() {
  const data = await executeQuery('SELECT COUNT(*) as posts, AVG(score) as avgScore, COUNT(DISTINCT author) as maskedUsers FROM prod_catalog.reddit.gold_metrics');
  if (!data || data.length === 0) return { posts: 'N/A', avgScore: 'N/A', maskedUsers: 'N/A' };
  
  return {
    posts: data[0].posts.toString(),
    avgScore: data[0].avgScore.toFixed(1).toString(),
    maskedUsers: data[0].maskedUsers.toString()
  };
}
