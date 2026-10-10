const { DBSQLClient } = require('@databricks/sql');
require('dotenv').config({ path: '../.env' }); // Load from root

async function test() {
  const host = process.env.DATABRICKS_HOST;
  const path = process.env.NEXT_PUBLIC_DATABRICKS_SQL_HTTP_PATH;
  const token = process.env.NEXT_PUBLIC_DATABRICKS_API_TOKEN;

  console.log("Creds:", host, path, token ? "SET" : "UNSET");

  const client = new DBSQLClient();
  try {
    await client.connect({
      host: host.replace('https://', '').replace(/\/$/, ''),
      path: path,
      token: token,
    });
    
    const session = await client.openSession();
    
    console.log("Executing query...");
    const queryOperation = await session.executeStatement(`
      SELECT 
        (SELECT COUNT(*) FROM prod_catalog.ethereum.bronze) as eth_count,
        (SELECT COUNT(*) FROM prod_catalog.github.bronze) as gh_count,
        (SELECT COUNT(*) FROM prod_catalog.overture.bronze) as ov_count,
        (SELECT MAX(created_at) FROM prod_catalog.github.bronze) as latest_gh
    `, { runAsync: true });
    
    const result = await queryOperation.fetchAll();
    console.log("Result:", result);
    
    await session.close();
    await client.close();
  } catch (error) {
    console.error("Node error:", error);
  }
}

test();
