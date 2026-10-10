'use server';

// ============================================================================
// DATABRICKS COMMUNITY EDITION (FREE TIER) PORTFOLIO FALLBACK
// ============================================================================
// Since Databricks Community Edition does not support Serverless SQL Warehouses,
// we cannot use the @databricks/sql driver to execute live queries here.
// To ensure the dashboard remains visually stunning for portfolio demonstrations,
// this Server Action returns highly realistic mock data matching the pipeline's scale.
// ============================================================================

export async function getEthereumMetrics() {
  await new Promise(resolve => setTimeout(resolve, 800));
  return {
    totalTransfers: '2,450,192 ETH',
    avgGas: '21,040',
    txCount: '15.2M'
  };
}

export async function getGithubMetrics() {
  await new Promise(resolve => setTimeout(resolve, 800));
  return {
    events: '8.4B',
    uniqueRepos: '45.2M',
    pushEvents: '4.1B'
  };
}

export async function getOvertureMetrics() {
  await new Promise(resolve => setTimeout(resolve, 800));
  return {
    pois: '502.1M',
    categories: '1,420',
    regions: '8,412'
  };
}

export async function getQuarantineMetrics() {
  await new Promise(resolve => setTimeout(resolve, 800));
  return [
    { _quarantine_reason: "lat/lon bounds check failed", _quarantine_timestamp: new Date().toISOString(), order_id: "OVR-819", customer_id: "N/A" },
    { _quarantine_reason: "customer_id IS NOT NULL failed", _quarantine_timestamp: new Date(Date.now() - 3600000).toISOString(), order_id: "ETH-991", customer_id: null },
    { _quarantine_reason: "schema inference fatal error", _quarantine_timestamp: new Date(Date.now() - 7200000).toISOString(), order_id: null, customer_id: "GH-882" }
  ];
}

export async function getPlatformMetrics() {
  await new Promise(resolve => setTimeout(resolve, 800));
  return {
    totalRecords: '17.5B+', // Adjusted down slightly since Reddit was removed
    ingestionRate: '6,100 msg/sec',
    computeNodes: '42 Workers'
  };
}
