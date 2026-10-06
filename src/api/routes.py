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
