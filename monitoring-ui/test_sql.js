const { DBSQLClient } = require('@databricks/sql');
require('dotenv').config();

async function test() {
  const client = new DBSQLClient();
  try {
    await client.connect({
      host: process.env.DATABRICKS_HOST.replace('https://', '').replace(/\/$/, ''),
      path: process.env.NEXT_PUBLIC_DATABRICKS_SQL_HTTP_PATH || process.env.DATABRICKS_SQL_HTTP_PATH,
      token: process.env.DATABRICKS_TOKEN || process.env.NEXT_PUBLIC_DATABRICKS_API_TOKEN,
    });
    const session = await client.openSession();
    
    console.log("Testing individual tables...");
    
    try {
        const eth = await session.executeStatement('SELECT COUNT(*) FROM prod_catalog.ethereum.bronze', { runAsync: true });
        console.log("Ethereum:", await eth.fetchAll());
    } catch(e) { console.error("Ethereum missing:", e.message) }
    
    try {
        const gh = await session.executeStatement('SELECT COUNT(*) FROM prod_catalog.github.bronze', { runAsync: true });
        console.log("Github:", await gh.fetchAll());
    } catch(e) { console.error("Github missing:", e.message) }

    try {
        const ov = await session.executeStatement('SELECT COUNT(*) FROM prod_catalog.overture.bronze', { runAsync: true });
        console.log("Overture:", await ov.fetchAll());
    } catch(e) { console.error("Overture missing:", e.message) }

    await session.close();
    await client.close();
  } catch (error) {
    console.error("Connection error:", error.message);
  }
}

test();
