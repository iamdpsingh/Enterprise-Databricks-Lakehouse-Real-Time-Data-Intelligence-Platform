const { DBSQLClient } = require('@databricks/sql');
require('dotenv').config();

async function test() {
  const host = process.env.DATABRICKS_HOST;
  const path = process.env.NEXT_PUBLIC_DATABRICKS_SQL_HTTP_PATH;
  const token = process.env.NEXT_PUBLIC_DATABRICKS_API_TOKEN;

  console.log("Connecting using:", { host, path });

  const client = new DBSQLClient();
  try {
    await client.connect({
      host: host.replace('https://', '').replace(/\/$/, ''),
      path: path,
      token: token,
    });
    
    const session = await client.openSession();
    
    console.log("Testing Platform Query...");
    try {
        const queryOperation = await session.executeStatement(`
          SELECT 
            (SELECT COUNT(*) FROM prod_catalog.ethereum.bronze) as eth_count,
            (SELECT COUNT(*) FROM prod_catalog.github.bronze) as gh_count,
            (SELECT COUNT(*) FROM prod_catalog.overture.bronze) as ov_count,
            (SELECT MAX(created_at) FROM prod_catalog.github.bronze) as latest_gh
        `, { runAsync: true });
        
        const result = await queryOperation.fetchAll();
        console.log("Platform Result:", result);
    } catch(e) {
        console.error("Platform Query Error:", e.message);
    }

    console.log("Testing Ethereum Query...");
    try {
        const q2 = await session.executeStatement('SELECT COUNT(*) as txCount, AVG(CAST(gas AS DOUBLE)) as avgGas, SUM(CAST(value AS DOUBLE)) as totalTransfers FROM prod_catalog.ethereum.bronze', { runAsync: true });
        console.log("Ethereum Result:", await q2.fetchAll());
    } catch(e) {
        console.error("Ethereum Query Error:", e.message);
    }

    await session.close();
    await client.close();
  } catch (error) {
    console.error("Connection Error:", error.message);
  }
}

test();
