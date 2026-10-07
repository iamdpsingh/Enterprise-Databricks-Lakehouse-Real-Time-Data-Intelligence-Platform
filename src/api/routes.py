from fastapi import APIRouter, Depends, HTTPException
from typing import Any, Dict

from .dependencies import get_databricks_connection
from src.utilities.logger import logger

router = APIRouter(prefix="/v1", tags=["Data Intelligence"])

@router.get("/metrics/customer/{customer_id}")
async def get_customer_metrics(
    customer_id: str,
    conn: Any = Depends(get_databricks_connection)
) -> Dict[str, Any]:
    """
    Fetches real-time aggregated metrics for a specific customer from the Gold layer.
    """
    logger.info(f"API Request: fetch metrics for customer {customer_id}")
    
    query = """
        SELECT total_lifetime_value, total_orders, first_order_date, last_order_date
        FROM main.gold.customer_metrics
        WHERE customer_id = ?
    """
    
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, (customer_id,))
            result = cursor.fetchone()
            
            if not result:
                raise HTTPException(status_code=404, detail="Customer not found in Gold layer")
                
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, result))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying Databricks: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal database error")

@router.get("/metrics/orders/summary")
async def get_orders_summary(
    conn: Any = Depends(get_databricks_connection)
) -> Dict[str, Any]:
    """
    Fetches real-time aggregated global order metrics from the Gold layer.
    This endpoint powers the top-level Next.js dashboard.
    """
    logger.info("API Request: fetch global order metrics summary")
    
    # In a real environment we'd query the Gold table we created: main.gold.order_metrics
    query = """
        SELECT 
            SUM(daily_revenue) as total_lifetime_value, 
            SUM(daily_order_count) as total_orders, 
            MAX(unique_customers) as active_users
        FROM main.gold.order_metrics
    """
    
    try:
        with conn.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchone()
            
            if not result or result[0] is None:
                # Return defaults if table is empty
                return {
                    "total_lifetime_value": 0,
                    "total_orders": 0,
                    "active_users": 0
                }
                
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, result))
            
    except Exception as e:
        logger.error(f"Error querying Databricks for order summary: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal database error")

@router.get("/metrics/quality/quarantine")
async def get_quarantine_records(
    limit: int = 10,
    conn: Any = Depends(get_databricks_connection)
) -> Dict[str, Any]:
    """
    Fetches the most recent quarantined records from the Silver layer.
    """
    logger.info(f"API Request: fetch top {limit} quarantined records")
    
    query = f"""
        SELECT _quarantine_reason, _quarantine_timestamp, order_id, customer_id
        FROM main.silver.quarantine_orders
        ORDER BY _quarantine_timestamp DESC
        LIMIT {limit}
    """
    
    try:
        with conn.cursor() as cursor:
            cursor.execute(query)
            results = cursor.fetchall()
            
            if not results:
                return {"records": []}
                
            columns = [desc[0] for desc in cursor.description]
            records = [dict(zip(columns, row)) for row in results]
            return {"records": records}
            
    except Exception as e:
        logger.error(f"Error querying Databricks for quarantine records: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal database error")
